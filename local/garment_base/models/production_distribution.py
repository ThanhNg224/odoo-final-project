from odoo import models, fields, api

class ProductionDistribution(models.Model):
    _name = 'production.distribution'
    _description = 'Production Distribution'

    allocate_qty = fields.Integer('Allocated Quantity', required=True)
    method = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic')
    ], string='Distribution Method', default='manual', required=True)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade') 