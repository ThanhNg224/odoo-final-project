from odoo import models, fields, api

class ProductionProcess(models.Model):
    _name = 'production.process'
    _description = 'Production Process'
    _order = 'sequence, id'

    name = fields.Char('Process Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    unit_price = fields.Float('Unit Price', digits=(12, 2))
    multiplier = fields.Float('Multiplier', default=1.0)
    quantity = fields.Integer('Quantity')
    note = fields.Text('Note')
    total_price = fields.Float('Total Price', compute='_compute_total_price', store=True)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    
    @api.depends('unit_price', 'multiplier', 'quantity')
    def _compute_total_price(self):
        for process in self:
            process.total_price = process.unit_price * process.multiplier * process.quantity 
    
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