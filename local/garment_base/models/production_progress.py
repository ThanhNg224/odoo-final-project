from odoo import models, fields, api

class ProductionProgress(models.Model):
    _name = 'production.progress'
    _description = 'Production Progress'
    _order = 'date desc'

    step_name = fields.Char('Step Name', required=True)
    completed_qty = fields.Integer('Completed Quantity', required=True)
    date = fields.Date('Date', default=fields.Date.today, required=True)
    note = fields.Text('Note')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
