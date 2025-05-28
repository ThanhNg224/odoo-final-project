from odoo import models, fields, api

class ProductionMaterial(models.Model):
    _name = 'production.material'
    _description = 'Production Material'

    name = fields.Char('Material Name', required=True)
    item_number = fields.Char('Item Number')
    specification = fields.Char('Specification')
    unit = fields.Char('Unit')
    location = fields.Char('Location')
    single_piece_qty = fields.Float('Single Piece Quantity')
    unit_loss = fields.Float('Unit Loss')
    quantity = fields.Float('Quantity')
    total_usage = fields.Float('Total Usage', compute='_compute_total_usage', store=True)
    unit_price = fields.Float('Unit Price', digits=(12, 2))
    supplier = fields.Char('Supplier/Source')
    image = fields.Binary("Material Image", attachment=True)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    
    @api.depends('quantity', 'single_piece_qty', 'unit_loss')
    def _compute_total_usage(self):
        for material in self:
            material.total_usage = material.quantity * (material.single_piece_qty + material.unit_loss) 
    
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