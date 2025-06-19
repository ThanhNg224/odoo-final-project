from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import json
import ast
import logging

_logger = logging.getLogger(__name__)

class ProductionOrder(models.Model):
    _name = 'production.order'
    _description = 'Production Order'

    code = fields.Char('Production Code', readonly=True, copy=False, default=lambda self: self._generate_production_code())
    name = fields.Char('Order Reference', required=True, unique=True, default=lambda self: 'New')
    planned_date = fields.Date('Planned Date', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string='Status', default='draft')
    finance_state = fields.Selection([
        ('waiting', 'Waiting Payment'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid')
    ], string='Finance Status', default='waiting')
    # Simple payment tracking
    payment_amount = fields.Float('Payment Received', default=0.0, help="Amount received from customer")
    payment_notes = fields.Text('Payment Notes', help="Notes about payments received")
    finance_approved_by = fields.Many2one('res.users', string='Finance Approved By', readonly=True)
    finance_approval_date = fields.Datetime('Finance Approval Date', readonly=True)
    cost_total = fields.Float('Total Cost', compute='_compute_cost_total', digits=(16, 2), store=True)
      # Sample related fields - Required field for production order
    sample_id = fields.Many2one('garment.sample', string='Sample')
    sample_name = fields.Char(string='Sample Name', store=True, compute='_compute_sample_fields')
    sample_code = fields.Char(string='Sample Code', store=True, compute='_compute_sample_fields')
    brand = fields.Char(related='sample_id.brand', string='Brand', readonly=True, store=True)
    development_date = fields.Date(related='sample_id.development_date', string='Development Date', readonly=True, store=True)
    designer = fields.Char(related='sample_id.designer', string='Designer', readonly=True, store=True)
    sample_color = fields.Char(related='sample_id.color', string='Color', readonly=True, store=True)
    
    # Additional fields from UI
    bed_number = fields.Integer('Bed Number', default=1)
    quantity = fields.Integer('Total Quantity', compute='_compute_total_quantity', store=True, default=0)
    client = fields.Char('Client', compute='_compute_order_fields', store=True)
    department = fields.Char('Department')
    salary_month = fields.Char('Salary Month')
    shipping_date = fields.Date('Shipping Date')
    delivery_date = fields.Date('Delivery Date', compute='_compute_order_fields', store=True)
    image = fields.Binary("Product Image", attachment=True)
    process_count = fields.Integer('Number of Processes', compute='_compute_process_count')
    process_requirements = fields.Text('Process Requirements')
    line_count = fields.Integer(compute='_compute_line_count', string='Line Count')
    total_other_cost = fields.Float('Total Other Costs', compute='_compute_total_other_cost', store=True)
    
    # Relationships
    style_id = fields.Many2one('product.style', string='Product Style')
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
    # — Link đến đơn hàng có sẵn từ module garment_base —
    garment_order_id = fields.Many2one(
        'garment.order',
        string='Đơn hàng',
        ondelete='set null',
        context={'default_state': 'confirmed'},
    )
    order_name    = fields.Char(string='Order Name', compute='_compute_order_fields', store=True)
    order_number  = fields.Char(string='Order Number', compute='_compute_order_fields', store=True)
    is_stored = fields.Boolean(string='Is Stored', default=False)   # Add this field to help with domain management
    available_sample_ids = fields.Many2many(
        'garment.sample', 
        compute='_compute_available_samples',
        string='Available Samples'
    )

    @api.depends('garment_order_id', 'garment_order_id.name', 'garment_order_id.code', 
                 'garment_order_id.issuing_company', 'garment_order_id.receiving_date')
    def _compute_order_fields(self):
        """Compute order-related fields to ensure they always stay in sync"""
        for record in self:
            if record.garment_order_id:
                record.order_name = record.garment_order_id.name
                record.order_number = record.garment_order_id.code
                record.client = record.garment_order_id.issuing_company
                record.delivery_date = record.garment_order_id.receiving_date
            else:
                record.order_name = False
                record.order_number = False
                record.client = False
                record.delivery_date = False

    # NEW COMPUTED FIELDS for Sample information
    @api.depends('sample_id', 'sample_id.name', 'sample_id.code')
    def _compute_sample_fields(self):
        """Compute sample-related fields to ensure they always stay in sync"""
        for record in self:
            if record.sample_id:
                record.sample_name = record.sample_id.name
                record.sample_code = record.sample_id.code
            else:
                record.sample_name = False
                record.sample_code = False
    
    @api.depends('garment_order_id', 'garment_order_id.sample_ids')
    def _compute_available_samples(self):
        for record in self:
            if record.garment_order_id and record.garment_order_id.sample_ids:
                record.available_sample_ids = record.garment_order_id.sample_ids
            else:
                record.available_sample_ids = self.env['garment.sample']  # Empty recordset

    @api.depends('line_ids', 'line_ids.planned_qty')
    def _compute_total_quantity(self):
        """Calculate total quantity from all order lines"""
        for order in self:
            total = sum(line.planned_qty for line in order.line_ids)
            order.quantity = total
            _logger.info(f"Computing quantity for order {order.name}: {total}")

    @api.onchange('garment_order_id')
    def _onchange_garment_order_id(self):
        result = {}
        
        if not self.garment_order_id:
            self.sample_id = False
            
            # Return empty domain
            result['domain'] = {'sample_id': [('id', '=', False)]}
            return result
        
        # Clear current sample selection when order changes
        self.sample_id = False
        
        # Get available samples
        available_samples = self.garment_order_id.sample_ids
        
        if not available_samples:
            # Show warning if no samples available
            result['warning'] = {
                'title': 'No Samples Available',
                'message': f'The selected order "{self.garment_order_id.name}" has no samples associated with it. Please add samples to this order first.'
            }
            result['domain'] = {'sample_id': [('id', '=', False)]}
        else:
            # Set domain to filter samples
            result['domain'] = {'sample_id': [('id', 'in', available_samples.ids)]}
        
        return result
    @api.onchange('sample_id')
    def _onchange_sample_id(self):
        if self.sample_id:
            # Check if selected sample belongs to the current order
            if self.garment_order_id and self.sample_id not in self.garment_order_id.sample_ids:
                return {
                    'warning': {
                        'title': 'Invalid Sample Selection',
                        'message': 'The selected sample does not belong to the current order. Please select a valid sample.'
                    },
                    'value': {'sample_id': False}
                }
            
            # Copy process requirements safely
            if hasattr(self.sample_id, 'technical_requirements') and self.sample_id.technical_requirements:
                self.process_requirements = self.sample_id.technical_requirements
            else:
                self.process_requirements = ''
        else:
            self.process_requirements = ''
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('order_name', operator, name)]
        return self._search(domain + args, limit=limit)
    
    
    @api.depends('progress_ids.completed_qty')
    def _compute_completed_quantity(self):
        for order in self:
            # Calculate total completed quantity from all order lines
            order.completed_quantity = sum(line.done_qty for line in order.line_ids)
    
    @api.depends('completed_quantity', 'line_ids.planned_qty')
    def _compute_progress_percentage(self):
        for order in self:
            total_planned = sum(line.planned_qty for line in order.line_ids)
            if total_planned > 0:
                order.progress_percentage = (order.completed_quantity / total_planned) * 100
                
                # Auto-update state based on progress
                if order.progress_percentage >= 100 and order.state == 'in_progress':
                    order.state = 'done'
                    _logger.info(f"Production order {order.name} automatically marked as 'done' - 100% complete")
                elif order.progress_percentage > 0 and order.state == 'draft':
                    # If there's progress but still in draft, move to in_progress
                    if order.finance_state != 'waiting' or order.payment_amount > 0:
                        order.state = 'in_progress'
                        _logger.info(f"Production order {order.name} automatically moved to 'in_progress'")
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
    
    def action_mark_waiting(self):
        """Mark as waiting for payment"""
        self.finance_state = 'waiting'
        return True
    
    def action_mark_partial_paid(self):
        """Mark as partially paid"""
        self.finance_state = 'partial'
        self.finance_approved_by = self.env.user
        self.finance_approval_date = fields.Datetime.now()
        return True
    
    def action_mark_fully_paid(self):
        """Mark as fully paid"""
        self.finance_state = 'paid'
        self.finance_approved_by = self.env.user
        self.finance_approval_date = fields.Datetime.now()
        return True
    
    def action_finance_wizard(self):
        """Open simple finance update wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Finance Status',
            'res_model': 'production.finance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
    
    # Action methods
    def set_in_progress(self):
        for record in self:
            if record.finance_state == 'waiting' and record.payment_amount <= 0:
                raise UserError("Cannot start production without any payment or finance approval!")
            record.state = 'in_progress'
            _logger.info(f"Production order {record.name} set to 'in_progress'")
        return True
    
    # Remove the set_done method since it's now automatic
    # def set_done(self):
    #     for record in self:
    #         record.state = 'done'
    #         _logger.info(f"Production order {record.name} set to 'done'")
    #     return True

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
        # Recompute total quantity after creating order lines
        self._compute_total_quantity()
        # Make sure to remove any "Other cost" entries that might have been created
        self.action_remove_other_cost_entries()
        
        return True

    def generate_bundles(self):
        Bundle = self.env['production.bundle']
        
        for order in self:
            # Clear existing bundles for this production order first
            existing_bundles = Bundle.search([('order_line_id.order_id', '=', order.id)])
            if existing_bundles:
                existing_bundles.unlink()
                _logger.info(f"Cleared {len(existing_bundles)} existing bundles for order {order.name}")
            
            # Get the next bundle counter after clearing
            bundle_counter = Bundle.search_count([]) + 1
            
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
            
            _logger.info(f"Generated new bundles for order {order.name}")
        
        return True

    def action_refresh_quantity(self):
        """Manually refresh the total quantity calculation"""
        self._compute_total_quantity()
        return True

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
        
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self._generate_production_code()
        return super().create(vals_list)

    
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

    def action_open_edit_form(self):
        """Open the edit form for the current record"""
        try:
            # Try to find the edit form view
            edit_view = self.env.ref('garment_production.view_production_order_form_edit', raise_if_not_found=False)
            if not edit_view:
                # Fallback to default form view if edit view not found
                edit_view = self.env.ref('garment_base.view_production_order_form', raise_if_not_found=False)
        except:
            edit_view = False
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Production Order',
            'res_model': 'production.order',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': edit_view.id if edit_view else False,
            'target': 'current',
            'context': dict(self.env.context),
        }

    def action_export_pdf(self):
        """Export production order as PDF"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'garment_production.report_production_order_template',
            'report_type': 'qweb-pdf',
            'data': {'ids': self.ids},
            'context': dict(self.env.context, active_ids=self.ids),
        }

    def _generate_production_code(self):
        # Get the next sequence number
        return self.env['ir.sequence'].next_by_code('production.order') or '/'


    def action_save_and_back(self):
        """Save the current record and return to the view-only form"""
        self.ensure_one()
        
        # Force save any pending changes
        if self.env.context.get('commit_other_cost_cleanup'):
            self.action_remove_other_cost_entries()
        
        try:
            # Try to find the view-only form
            view_form = self.env.ref('garment_production.view_production_order_form', raise_if_not_found=False)
            if not view_form:
                # Fallback to default form view if view-only form not found
                view_form = self.env.ref('garment_base.view_production_order_form', raise_if_not_found=False)
        except:
            view_form = False
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Production Order',
            'res_model': 'production.order',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_form.id if view_form else False,
            'target': 'main',  # Use 'main' instead of 'current' to replace current view
            'context': {'form_view_initial_mode': 'view'},  # Force view mode
        }

    def action_clean_material_entries(self):
        """Action to clean up invalid material entries"""
        for order in self:
            # Remove empty material entries
            self.env['production.material'].search([
                ('order_id', '=', order.id),
                '|', '|', '|',
                ('name', '=', False),
                ('name', '=', ''),
                ('unit_price', '<=', 0),
                ('quantity', '<=', 0)
            ]).unlink()
            
        return True

    def action_clean_process_entries(self):
        """Action to clean up invalid process entries"""
        for order in self:
            # Remove empty process entries
            self.env['production.process'].search([
                ('order_id', '=', order.id),
                '|', '|',
                ('name', '=', False),
                ('name', '=', ''),
                ('unit_price', '<=', 0)
            ]).unlink()
            
        return True


class GarmentSampleExtended(models.Model):
    _inherit = 'garment.sample'
    
    def name_get(self):
        result = []
        for sample in self:
            name = f"{sample.name} [{sample.code}]" if sample.code else sample.name
            result.append((sample.id, name))
        return result

    # Remove the duplicate methods that were incorrectly placed here
        for sample in self:
            name = f"{sample.name} [{sample.code}]" if sample.code else sample.name
            result.append((sample.id, name))
        return result

    # Remove the duplicate methods that were incorrectly placed here

