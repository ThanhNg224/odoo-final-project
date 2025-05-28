from odoo import models, fields, api

class ProductLot(models.Model):
    _name = 'product.lot'
    _description = 'Product Lot'

    lot_code = fields.Char('Lot Code', required=True, unique=True)
    quantity = fields.Integer('Quantity', required=True)
    note = fields.Text('Note')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    inout_ids = fields.One2many('stock.production.inout', 'lot_id', string='Stock Movements')