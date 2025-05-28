from odoo import models, fields, api

class StockProductionInOut(models.Model):
    _name = 'stock.production.inout'
    _description = 'Stock Production In/Out'
    _order = 'date desc'

    direction = fields.Selection([
        ('in', 'In'),
        ('out', 'Out')
    ], string='Direction', required=True)
    qty = fields.Integer('Quantity', required=True)
    date = fields.Date('Date', default=fields.Date.today, required=True)
    
    # Relationships
    lot_id = fields.Many2one('product.lot', string='Product Lot', required=True, ondelete='cascade') 