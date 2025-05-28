from odoo import models, fields, api

class OperationPrice(models.Model):
    _name = 'operation.price'
    _description = 'Operation Price'

    operation_name = fields.Char('Operation Name', required=True)
    unit_price = fields.Float('Unit Price', required=True, digits=(12, 2))
    description = fields.Text('Description')
    
    # Relationships
    order_ids = fields.One2many('production.order', 'price_policy_id', string='Production Orders')
    worker_entry_ids = fields.One2many('production.worker.entry', 'operation_id', string='Worker Entries')