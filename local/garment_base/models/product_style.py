from odoo import models, fields, api

class ProductStyle(models.Model):
    _name = 'product.style'
    _description = 'Product Style'

    code = fields.Char('Code', required=True, unique=True)
    name = fields.Char('Name', required=True)
    season = fields.Char('Season')
    description = fields.Text('Description')
    
    # Additional fields from UI
    image = fields.Binary("Style Image", attachment=True)
    shape = fields.Char('Shape')
    material = fields.Char('Material')
    
    # Relationships
    order_ids = fields.One2many('production.order', 'style_id', string='Production Orders') 