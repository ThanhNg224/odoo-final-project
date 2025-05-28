from odoo import models, fields, api

class ProductionBundle(models.Model):
    _name = 'production.bundle'
    _description = 'Production Bundle'

    bundle_no = fields.Char('Bundle Number', required=True, unique=True)
    size = fields.Char('Size', required=True)
    qty = fields.Integer('Quantity', required=True)
    ticket_printed = fields.Boolean('Ticket Printed', default=False)
    
    # Relationships
    order_line_id = fields.Many2one('production.order.line', string='Order Line', required=True, ondelete='cascade')
    
    # Related fields - fix these
    sample_name = fields.Char(related='order_line_id.sample_name', string="Sample", readonly=True)
    client = fields.Char(related='order_line_id.client', string="Client", readonly=True)
    color = fields.Char(related='order_line_id.color', string="Color", readonly=True)