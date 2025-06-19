from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InventoryColor(models.Model):
    _name = 'garment.inventory.color'
    _description = 'Inventory Color'

    code = fields.Char(string='Color Code')
    name = fields.Char(string='Color')

class InventoryMaterialColorQuantity(models.Model):
    _name = 'garment.inventory.material.color.quantity'
    _description = 'Inventory Material Color Quantity'
    
    material_id = fields.Many2one('garment.inventory.material', string='Material')
    color_id = fields.Many2one('garment.inventory.color', string='Color')
    quantity_on_hand = fields.Float(string='Quantity on Hand', default=0.0)
    quantity_reserved = fields.Float(string='Quantity Reserved', default=0.0)
    quantity_available = fields.Float(string='Quantity Available', compute='_compute_quantity_available', store=True)
    
    @api.depends('quantity_on_hand', 'quantity_reserved')
    def _compute_quantity_available(self):
        for record in self:
            record.quantity_available = record.quantity_on_hand - record.quantity_reserved

    @api.constrains('quantity_on_hand', 'quantity_reserved')
    def _check_quantity_constraints(self):
        for record in self:
            if record.quantity_reserved > record.quantity_on_hand:
                raise ValidationError(_('Reserved quantity cannot be greater than quantity on hand.'))


class InventoryMaterial(models.Model):
    _name = 'garment.inventory.material'
    _description = 'Inventory Material'

    code = fields.Char(string='Material Code')
    name = fields.Char(string='Material Name')
    unit = fields.Char(string='Unit')
    color_quantity_ids = fields.One2many('garment.inventory.material.color.quantity', 'material_id', string='Color Quantities')
    supplier = fields.Char(string='Suppliers')
    inventory_location = fields.Char(string='Inventory Location')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    unit_price = fields.Float(string='Unit Price', default=0.0)
    remarks = fields.Html(string='Remarks')


class InventoryReceiptLine(models.Model):
    _name = 'garment.receipt.line'
    _description = 'Inventory Receipt Line'

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    serial_number = fields.Char(string='Serial Number', copy=False, default=lambda self: self._generate_serial_number())
    type = fields.Selection([
        ('in', 'In'),
        ('out', 'Out')
    ], string='Type', required=True, default='in')
    publisher = fields.Many2one('res.users', string='Publisher', default=lambda self: self.env.user)
    publish_date = fields.Date(string='Publish Date', default=fields.Date.context_today)
    method = fields.Char(string='Method', default='manual')
    item_type = fields.Selection([
        ('sample', 'Sample'),
        ('order', 'Order'),
        ('production', 'Production'),
        ('material', 'Material'),
        ('other', 'Other')
    ], string='Item Type', default='other')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    item_id = fields.Char(string='Item ID', help="ID of the related item (e.g., sample ID, order ID, production ID)")
    remark = fields.Char(string='Remark')

    # Material specific fields
    material_id = fields.Many2one('garment.inventory.material', string='Material')
    color_id = fields.Many2one('garment.inventory.color', string='Color')
    from_type = fields.Selection([
        ('sample', 'Sample'),
        ('order', 'Order'),
        ('production', 'Production'),
        ('material', 'Material'),
        ('other', 'Other')
    ], string='From Type', default='other', invisible=True)
    receiving_company = fields.Char(string='Receiving Company')
    used_quantity = fields.Float(string='Quantity')
    defective_quantity = fields.Float(string='Defective Quantity', default=0.0)
    unit_price = fields.Float(string='Unit Price')
    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)

    # Invisible fields
    available_color_ids = fields.Many2many('garment.inventory.color', string='Available Colors', compute='_compute_available_color_ids')
    
    @api.depends('material_id', 'material_id.color_quantity_ids', 'type')
    def _compute_available_color_ids(self):
        for record in self:
            if record.type == 'out':
                record.available_color_ids = record.material_id.color_quantity_ids.mapped('color_id')
            else:
                record.available_color_ids = self.env['garment.inventory.color'].search([])

    @api.depends('used_quantity', 'defective_quantity', 'unit_price', 'item_type')
    def _compute_total_price(self):
        for record in self:
            if record.item_type == 'material':
                record.total_price = (record.used_quantity + record.defective_quantity) * record.unit_price
            else:
                record.total_price = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('serial_number'):
                vals['serial_number'] = self._generate_serial_number()
        return super().create(vals_list)

    def _generate_serial_number(self):
        return self.env['ir.sequence'].next_by_code('garment.receipt.line') or '/'

    def write(self, vals):
        result = super().write(vals)
        return result
    
    def action_mark_confirmed(self):
        for record in self:
            if record.state != 'draft':
                continue
            result = record.handle_receipt_line(record.item_type, record.item_id, record.type)
            if result:
                record.write({'state': 'confirmed'})
            
            # Show success notification using Odoo's bus notification system
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                {
                    'title': _('Success'),
                    'message': _('Receipt line "%s" has been successfully confirmed.') % record.serial_number,
                    'type': 'success',
                    'sticky': False,
                    'fadeout': 2000,
                }
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Waiting Receipts'),
            'res_model': 'garment.receipt.line',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_inventory.view_garment_receipt_line_tree_waiting').id, 'tree'),
                (self.env.ref('garment_inventory.view_garment_receipt_line_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('state', '=', 'draft')],
            'context': {
                'form_view_ref': 'garment_inventory.view_garment_receipt_line_form_view',
                'create_view_ref': 'garment_inventory.view_garment_receipt_line_form_edit',
                'tree_view_ref': 'garment_inventory.view_garment_receipt_line_tree_waiting'
            },
        }

    def action_mark_cancelled(self):
        for record in self:
            if record.state != 'draft':
                continue
            record.write({'state': 'cancelled'})
            
            # Set is_waiting_for_approval to False for all item types
            match record.item_type:
                case 'sample':
                    sample = self.env['garment.sample'].browse(int(record.item_id))
                    if sample.exists():
                        sample.write({'is_waiting_for_approval': False})
                case 'order':
                    order = self.env['garment.order'].browse(int(record.item_id))
                    if order.exists():
                        order.write({'is_waiting_for_approval': False})
                case 'production':
                    production = self.env['production.order'].browse(int(record.item_id))
                    if production.exists():
                        production.write({'is_waiting_for_approval': False})
                case _:
                    pass

            # Show success notification
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                {
                    'title': _('Success'),
                    'message': _('Receipt line "%s" has been successfully cancelled.') % record.serial_number,
                    'type': 'success',
                    'sticky': False,
                    'fadeout': 2000,
                }
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Waiting Receipts'),
            'res_model': 'garment.receipt.line',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_inventory.view_garment_receipt_line_tree_waiting').id, 'tree'),
                (self.env.ref('garment_inventory.view_garment_receipt_line_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('state', '=', 'draft')],
            'context': {
                'form_view_ref': 'garment_inventory.view_garment_receipt_line_form_view',
                'create_view_ref': 'garment_inventory.view_garment_receipt_line_form_edit',
                'tree_view_ref': 'garment_inventory.view_garment_receipt_line_tree_waiting'
            },
        }
    
    def handle_receipt_line(self, item_type, item_id, receipt_line_type):
        match item_type:
            case 'sample':
                sample = self.env['garment.sample'].browse(int(item_id))
                if sample.exists():
                    match receipt_line_type:
                        case 'in':
                            sample.write({'is_stored': True})
                            sample.write({'is_waiting_for_approval': False})
                            return True
                        case 'out':
                            sample.write({'is_stored': False})
                            sample.write({'is_waiting_for_approval': False})
                            return True
                            
            case 'order':
                order = self.env['garment.order'].browse(int(item_id))
                if order.exists():
                    match receipt_line_type:
                        case 'in':
                            order.write({'is_stored': True})
                            order.write({'is_waiting_for_approval': False})
                            return True
                        case 'out':
                            order.write({'is_stored': False})
                            order.write({'is_waiting_for_approval': False})
                            return True
                            
            case 'production':
                production = self.env['production.order'].browse(int(item_id))
                if production.exists():
                    match receipt_line_type:
                        case 'in':
                            production.write({'is_stored': True})
                            production.write({'is_waiting_for_approval': False})
                            return True
                        case 'out':
                            production.write({'is_stored': False})
                            production.write({'is_waiting_for_approval': False})
                            return True
            case 'material':
                # Handle material inventory operations
                try:
                    material_id = self.material_id.id if self.material_id else None
                    color_id = self.color_id.id if self.color_id else None
                    total_quantity = self.used_quantity + self.defective_quantity
                    
                    match receipt_line_type:
                        case 'in':
                            # Case 'in': Add material to inventory
                            
                            # Ensure material exists, create if not
                            if not material_id:
                                raise ValidationError(_('Material is required for material receipt'))
                            
                            # Ensure color exists, create if not  
                            if not color_id:
                                raise ValidationError(_('Color is required for material receipt'))
                            
                            # Find or create InventoryMaterialColorQuantity record
                            material_color_qty = self.env['garment.inventory.material.color.quantity'].search([
                                ('material_id', '=', material_id),
                                ('color_id', '=', color_id)
                            ], limit=1)
                            
                            if material_color_qty:
                                # If exists, add to existing quantity
                                material_color_qty.write({
                                    'quantity_on_hand': material_color_qty.quantity_on_hand + total_quantity,
                                    # Override unit price if provided
                                    'unit_price': material_color_qty.unit_price if material_color_qty.unit_price > 0 else self.unit_price
                                })
                            else:
                                # If not exists, create new record
                                self.env['garment.inventory.material.color.quantity'].create({
                                    'material_id': material_id,
                                    'color_id': color_id,
                                    'quantity_on_hand': total_quantity,
                                    'quantity_reserved': 0.0
                                })
                            
                            return True
                            
                        case 'out':
                            # Case 'out': Remove material from inventory
                            
                            # Check if material and color exist
                            if not material_id or not color_id:
                                raise ValidationError(_('Material and color must exist for material outgoing'))
                            
                            # Find the material-color quantity record
                            material_color_qty = self.env['garment.inventory.material.color.quantity'].search([
                                ('material_id', '=', material_id),
                                ('color_id', '=', color_id)
                            ], limit=1)
                            
                            if not material_color_qty:
                                raise ValidationError(_('Material with specified color does not exist in inventory'))
                            
                            # Check if there's enough quantity available
                            if material_color_qty.quantity_available < total_quantity:
                                raise ValidationError(_('Insufficient material quantity. Available: %s, Required: %s') % (
                                    material_color_qty.quantity_available, total_quantity))
                            
                            # Deduct quantity from inventory
                            material_color_qty.write({
                                'quantity_on_hand': material_color_qty.quantity_on_hand - total_quantity
                            })
                            
                            return True
                            
                except ValidationError:
                    # Re-raise ValidationError to show proper error messages
                    raise
                except Exception as e:
                    raise ValidationError(_('Error processing material inventory: %s') % str(e))
            case 'other':
                pass
                
            case _:
                # Handle unknown item types
                pass
