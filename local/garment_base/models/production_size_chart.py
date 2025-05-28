from odoo import models, fields, api

class ProductionSizeChart(models.Model):
    _name = 'production.size.chart'
    _description = 'Production Size Chart'

    row_number = fields.Integer('Row Number')
    column = fields.Char('Column')
    value = fields.Char('Value')
    image = fields.Binary("Size Chart Image", attachment=True)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade') 