from odoo import models, fields, api
from datetime import datetime
import json
import ast
import logging

_logger = logging.getLogger(__name__)

class ProductionOrder(models.Model):
    _name = 'production.order'
    _description = 'Production Order'

    name = fields.Char('Order Reference', required=True, unique=True, default=lambda self: 'New')
    planned_date = fields.Date('Planned Date', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string='Status', default='draft')
    finance_state = fields.Selection([
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], string='Finance Status', default='waiting')
    cost_total = fields.Float('Total Cost', compute='_compute_cost_total', digits=(16, 2), store=True)
    
    # Sample related fields - Required field for production order
    sample_id = fields.Many2one('garment.sample', string='Sample', required=True)
    sample_name = fields.Char(string='Sample Name', store=True)
    sample_number = fields.Char(string='Sample Number', store=True)
    brand = fields.Char(related='sample_id.brand', string='Brand', readonly=True, store=True)
    development_date = fields.Date(related='sample_id.development_date', string='Development Date', readonly=True, store=True)
    designer = fields.Char(related='sample_id.designer', string='Designer', readonly=True, store=True)
    sample_color = fields.Char(related='sample_id.color', string='Color', readonly=True, store=True)
    
    # Additional fields from UI
    bed_number = fields.Integer('Bed Number', default=1)
    quantity = fields.Integer('Quantity', default=0)
    client = fields.Char('Client')
    department = fields.Char('Department')
    salary_month = fields.Char('Salary Month')
    shipping_date = fields.Date('Shipping Date')
    delivery_date = fields.Date('Delivery Date')
    image = fields.Binary("Product Image", attachment=True)
    process_count = fields.Integer('Number of Processes', compute='_compute_process_count')
    process_requirements = fields.Text('Process Requirements')
    line_count = fields.Integer(compute='_compute_line_count', string='Line Count')
    total_other_cost = fields.Float('Total Other Costs', compute='_compute_total_other_cost', store=True)
    
    # Relationships
    style_id = fields.Many2one('product.style', string='Product Style', required=False)
    price_policy_id = fields.Many2one('operation.price', string='Price Policy')
    line_ids = fields.One2many('production.order.line', 'order_id', string='Order Lines')
    progress_ids = fields.One2many('production.progress', 'order_id', string='Progress Entries')
    distribution_ids = fields.One2many('production.distribution', 'order_id', string='Distributions')
    process_ids = fields.One2many('production.process', 'order_id', string='Processes')
    cost_ids = fields.One2many('production.cost', 'order_id', string='Costs')
    material_ids = fields.One2many('production.material', 'order_id', string='Materials')
    
    # Calculate total progress
    completed_quantity = fields.Integer(compute='_compute_completed_quantity', string='Completed')
    progress_percentage = fields.Float(compute='_compute_progress_percentage', string='Progress %')
    
    # Cost calculations
    total_material_cost = fields.Float('Total Material Cost', compute='_compute_material_cost', store=True)
    total_process_cost = fields.Float('Total Process Cost', compute='_compute_process_cost', store=True)
    
    # Order related fields - to be connected to Order module later
    order_name = fields.Char(string='Order Name')
    order_number = fields.Char(string='Order Number')
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('number', operator, name)]
        return self.env['garment.sample'].search(domain + args, limit=limit).name_get()
    
    @api.onchange('sample_id')
    def _onchange_sample_id(self):
        if self.sample_id:
            self.sample_name = self.sample_id.name
            self.sample_number = self.sample_id.number
            
            # Copy process requirements
            self.process_requirements = self.sample_id.process_requirements
            
            # Remove any "Other cost" entries that might be created
            # This will be executed when the form is saved due to onchange limitations
            self.with_context(commit_other_cost_cleanup=True).update({'sample_id': self.sample_id.id})
            
            # Try to clean up invalid entries immediately
            self.action_remove_other_cost_entries()
    
    @api.onchange('sample_name')
    def _onchange_sample_name(self):
        if self.sample_name:
            samples = self.env['garment.sample'].search([('name', 'ilike', self.sample_name)])
            return {'domain': {'sample_id': [('id', 'in', samples.ids)]}}
    
    @api.onchange('sample_number')
    def _onchange_sample_number(self):
        if self.sample_number:
            samples = self.env['garment.sample'].search([('number', 'ilike', self.sample_number)])
            return {'domain': {'sample_id': [('id', 'in', samples.ids)]}}
    
    @api.depends('progress_ids.completed_qty')
    def _compute_completed_quantity(self):
        for order in self:
            if order.progress_ids:
                # Get the latest progress entry for each step
                steps = {}
                for progress in order.progress_ids:
                    if progress.step_name not in steps or progress.date > steps[progress.step_name].date:
                        steps[progress.step_name] = progress
                
                # Use the minimum completed quantity across all steps
                if steps:
                    order.completed_quantity = min(step.completed_qty for step in steps.values())
                else:
                    order.completed_quantity = 0
            else:
                order.completed_quantity = 0
    
    @api.depends('completed_quantity', 'quantity')
    def _compute_progress_percentage(self):
        for order in self:
            if order.quantity > 0:
                order.progress_percentage = (order.completed_quantity / order.quantity) * 100
            else:
                order.progress_percentage = 0
    
    @api.depends('process_ids')
    def _compute_process_count(self):
        for order in self:
            order.process_count = len(order.process_ids)
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = 0  # Set to 0 to prevent it from showing in the UI
    
    @api.depends('cost_ids')
    def _compute_total_other_cost(self):
        for order in self:
            other_costs = order.cost_ids.filtered(lambda c: c.cost_type == 'other')
            
            # No need to filter out "Other cost" entries anymore
            total_other_cost = sum(cost.amount for cost in other_costs)
            order.total_other_cost = total_other_cost
    
    @api.depends('material_ids.unit_price', 'material_ids.quantity', 'material_ids.total_usage')
    def _compute_material_cost(self):
        for order in self:
            total_material_cost = 0
            for material in order.material_ids:
                # Calculate cost based on unit price and total usage (or quantity if total_usage is 0)
                usage = material.total_usage if material.total_usage > 0 else material.quantity
                total_material_cost += material.unit_price * usage
            order.total_material_cost = total_material_cost
    
    @api.depends('process_ids.total_price')
    def _compute_process_cost(self):
        for order in self:
            order.total_process_cost = sum(process.total_price for process in order.process_ids)
    
    @api.depends('total_material_cost', 'total_process_cost', 'total_other_cost')
    def _compute_cost_total(self):
        for order in self:
            order.cost_total = order.total_material_cost + order.total_process_cost + order.total_other_cost
    
    # Action methods
    def set_in_progress(self):
        for record in self:
            record.state = 'in_progress'
        return True
    
    def set_done(self):
        for record in self:
            record.state = 'done'
        return True
        
    def action_view_lines(self):
        self.ensure_one()
        return {
            'name': 'Order Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'production.order.line',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }
        
    def action_view_processes(self):
        self.ensure_one()
        return {
            'name': 'Processes',
            'type': 'ir.actions.act_window',
            'res_model': 'production.process',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def generate_order_lines_from_sample(self):
        """Extract size data directly from sample and create order lines."""
        if not self.sample_id or not self.sample_id.finished_product_size:
            return
            
        # Clear existing order lines
        self.line_ids.unlink()
            
        # Get size data from sample
        size_data = self.sample_id.finished_product_size
        _logger.info(f"Sample size data for order lines: {size_data}")
        
        # Handle string data
        if isinstance(size_data, str):
            try:
                size_data = json.loads(size_data)
            except Exception as e:
                _logger.error(f"Error parsing size data: {e}")
                try:
                    import ast
                    size_data = ast.literal_eval(size_data)
                except Exception:
                    size_data = []
        
        # Extract sizes from the first column and create order lines
        if isinstance(size_data, list) and len(size_data) > 1:
            for i in range(1, len(size_data)):  # Skip header row
                row = size_data[i]
                if isinstance(row, list) and len(row) > 0:
                    size_value = row[0]
                    if size_value:
                        self.env['production.order.line'].create({
                            'order_id': self.id,
                            'size': size_value,
                            'planned_qty': 0,  # Default to 0, user will input quantities
                            'color': self.sample_id.color or '',  # Set color from sample
                        })
                        _logger.info(f"Created order line for size: {size_value}")
        
        # Make sure to remove any "Other cost" entries that might have been created
        self.action_remove_other_cost_entries()
        
        return True

    def generate_bundles(self):
        Bundle = self.env['production.bundle']
        bundle_counter = self.env['production.bundle'].search_count([]) + 1

        for order in self:
            for line in order.line_ids:
                size = line.size
                qty_remaining = line.planned_qty

                # Convention: each bundle contains 20 items (customizable)
                bundle_size = 20
                while qty_remaining > 0:
                    current_qty = min(bundle_size, qty_remaining)
                    bundle_no = f"B{bundle_counter}"

                    Bundle.create({
                        'bundle_no': bundle_no,
                        'size': size,
                        'qty': current_qty,
                        'order_line_id': line.id,
                    })

                    bundle_counter += 1
                    qty_remaining -= current_qty

    def copy_sample_data(self):
        """Copy material and process data from the sample to this production order."""
        if not self.sample_id:
            return
            
        # Copy material details
        if self.sample_id.material_detail:
            # Remove existing materials
            self.material_ids.unlink()
            
            material_data = self.sample_id.material_detail
            # Handle different input formats
            if isinstance(material_data, str):
                try:
                    material_data = json.loads(material_data)
                except Exception:
                    pass
                    
            if isinstance(material_data, list) and len(material_data) > 1:
                # Skip header row (material_data[0])
                for i in range(1, len(material_data)):
                    row = material_data[i]
                    if row and len(row) >= 8:  # Make sure there's enough data in the row
                        self.env['production.material'].create({
                            'order_id': self.id,
                            'name': row[0] if row[0] else '',  # Material Name
                            'item_number': row[1] if row[1] else '',  # Material Code
                            'specification': row[4] if row[4] else '',  # Specification
                            'unit': row[5] if row[5] else '',  # Unit
                            'location': row[6] if row[6] else '',  # Position
                            'single_piece_qty': float(row[7]) if row[7] and str(row[7]).replace('.','',1).isdigit() else 0.0,  # Quantity per Item
                            'unit_loss': float(row[8]) if len(row) > 8 and row[8] and str(row[8]).replace('.','',1).isdigit() else 0.0,  # Loss per Item
                        })
        
        # Copy process table
        if self.sample_id.process_table:
            # Remove existing processes
            self.process_ids.unlink()
            
            process_data = self.sample_id.process_table
            # Handle different input formats
            if isinstance(process_data, str):
                try:
                    process_data = json.loads(process_data)
                except Exception:
                    pass
                    
            if isinstance(process_data, list):
                for item in process_data:
                    if isinstance(item, dict) and 'name' in item:
                        self.env['production.process'].create({
                            'order_id': self.id,
                            'name': item.get('name', ''),
                            'unit_price': float(item.get('unit_price', 0)),
                            'multiplier': float(item.get('multiplier', 1)),
                            'note': item.get('notes', '') or item.get('note', '')
                        })
        
        # Copy other costs
        if self.sample_id.other_cost:
            self.update_other_costs_from_sample()
        
    def update_other_costs_from_sample(self):
        """Import other costs from the sample to this production order."""
        if not self.sample_id or not self.sample_id.other_cost:
            return
            
        # Remove existing 'other' type costs
        self.env['production.cost'].search([
            ('order_id', '=', self.id),
            ('cost_type', '=', 'other')
        ]).unlink()
        
        other_cost_data = self.sample_id.other_cost
        # Handle different input formats
        if isinstance(other_cost_data, str):
            try:
                other_cost_data = json.loads(other_cost_data)
            except Exception:
                pass
        
        # Create individual production.cost records for Other Costs tab
        total_other_cost = 0
        if isinstance(other_cost_data, list):
            for item in other_cost_data:
                if isinstance(item, dict) and 'cost_name' in item and 'amount' in item:
                    cost_name = item.get('cost_name', '').strip()
                    amount = float(item.get('amount', 0))
                    
                    # Skip empty entries, entries with zero amount, or entries named "Other cost"
                    if not cost_name or amount <= 0 or cost_name.lower() == 'other cost':
                        continue
                        
                    # Add to total
                    total_other_cost += amount
                    
                    # Create individual record
                    self.env['production.cost'].create({
                        'order_id': self.id,
                        'cost_type': 'other',
                        'amount': amount,
                        'note': cost_name
                    })
        
        return True

    def update_cost_summary(self):
        """No longer needed - Costs tab now uses computed fields directly"""
        pass

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('production.order') or 'P0001'
            
        record = super(ProductionOrder, self).create(vals)
        
        # If sample_id is set, immediately copy the sample data
        if record.sample_id:
            record.copy_sample_data()
            
            # Clean up any duplicate entries
            record.action_remove_other_cost_entries()
        
        return record
    
    def write(self, vals):
        # Check if we're setting a new sample
        previous_sample = self.sample_id
        result = super(ProductionOrder, self).write(vals)
        
        # If sample_id is changed, copy the sample data
        new_sample = vals.get('sample_id')
        if new_sample and new_sample != previous_sample.id:
            self.copy_sample_data()
            
        # Check if we need to clean up "Other cost" entries
        if self.env.context.get('commit_other_cost_cleanup'):
            self.action_remove_other_cost_entries()
        
        return result

    @api.model
    def create_from_sample(self, vals, sample_id):
        """Create a production order from a sample."""
        sample = self.env['garment.sample'].browse(sample_id)
        if not sample:
            return self.create(vals)
            
        # Create the production order
        vals['sample_id'] = sample.id
        
        # Create the production order
        order = self.create(vals)
        
        # Copy other data from the sample
        order.copy_sample_data()
        
        return order

    def action_remove_other_cost_entries(self):
        """Action to clean up invalid other cost entries"""
        for order in self:
            # Remove empty entries, entries with zero amount, or entries named "Other cost"
            self.env['production.cost'].search([
                ('order_id', '=', order.id),
                ('cost_type', '=', 'other'),
                '|', '|',
                ('note', '=', False),
                ('note', 'ilike', 'other cost'),
                ('amount', '<=', 0)
            ]).unlink()
            
            # Remove any old summary records from database (no longer needed)
            self.env['production.cost'].search([
                ('order_id', '=', order.id),
                ('note', 'in', ['Other costs from sample', 'Total Other Cost', 'Material Cost', 'Process Cost'])
            ]).unlink()
            
            # Remove records with invalid cost_type values
            self.env['production.cost'].search([
                ('order_id', '=', order.id),
                ('cost_type', 'in', ['total_other_cost', 'material_cost', 'process_cost'])
            ]).unlink()
            
            # Get remaining other cost entries to check for duplicates
            other_costs = self.env['production.cost'].search([
                ('order_id', '=', order.id),
                ('cost_type', '=', 'other')
            ])
            
            # Find duplicates by note (cost name)
            cost_names = {}
            duplicates = []
            
            for cost in other_costs:
                if cost.note in cost_names:
                    duplicates.append(cost.id)
                else:
                    cost_names[cost.note] = cost.id
            
            # Delete duplicates
            if duplicates:
                self.env['production.cost'].browse(duplicates).unlink()
                
        return True

    def action_cleanup_all_invalid_costs(self):
        """Clean up all invalid cost records across all production orders"""
        # Remove records with invalid cost_type values globally
        invalid_costs = self.env['production.cost'].search([
            ('cost_type', 'in', ['total_other_cost', 'material_cost', 'process_cost'])
        ])
        
        if invalid_costs:
            invalid_costs.unlink()
            
        # Remove summary records by note
        summary_costs = self.env['production.cost'].search([
            ('note', 'in', ['Other costs from sample', 'Total Other Cost', 'Material Cost', 'Process Cost'])
        ])
        
        if summary_costs:
            summary_costs.unlink()
            
        return True

class GarmentSampleExtended(models.Model):
    _inherit = 'garment.sample'
    
    def name_get(self):
        result = []
        for sample in self:
            name = f"{sample.name} [{sample.number}]" if sample.number else sample.name
            result.append((sample.id, name))
        return result

