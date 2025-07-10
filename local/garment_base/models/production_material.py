from odoo import models, fields, api

class ProductionMaterial(models.Model):
    _name = 'production.material'
    _description = 'Production Material'

    # Basic Information (matching sample structure)
    name = fields.Char('Material Name', required=True)
    item_number = fields.Char('Material Code')  # Renamed to match sample
    color = fields.Char('Color')
    color_code = fields.Char('Color Code')
    specification = fields.Char('Specification')
    unit = fields.Char('Unit')
    part = fields.Char('Part')  # Added to match sample
    
    # Quantity fields (matching sample calculation structure)
    single_piece_qty = fields.Float('Quantity per Unit', digits=(12, 4))  # Renamed for clarity
    unit_loss = fields.Float('Loss per Unit', digits=(12, 4))
    quantity = fields.Float('Unit Quantity', digits=(12, 2))  # This is the production quantity
    total_usage = fields.Float('Total Quantity Used', compute='_compute_total_usage', store=True, digits=(12, 4))
    
    # Price and Source
    unit_price = fields.Float('Unit Price', digits=(12, 2))
    supplier = fields.Char('Supplier')
    
    # Additional fields
    location = fields.Char('Location')  # Kept for compatibility
    image = fields.Binary("Material Image", attachment=True)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    
    @api.depends('quantity', 'single_piece_qty', 'unit_loss')
    def _compute_total_usage(self):
        """Calculate total usage using the same formula as Sample Material Detail:
        Total Quantity Used = (Quantity per Unit + Loss per Unit) * Unit Quantity
        """
        for material in self:
            qty_per_unit = material.single_piece_qty or 0.0
            loss_per_unit = material.unit_loss or 0.0  
            unit_quantity = material.quantity or 0.0
            
            # Same calculation as sample material detail table
            material.total_usage = (qty_per_unit + loss_per_unit) * unit_quantity
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        return result
    
    def write(self, vals):
        result = super().write(vals)
        return result
    
    def unlink(self):
        result = super().unlink()
        return result 