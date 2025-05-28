from odoo import models, fields, api

class ProductionWorkerEntry(models.Model):
    _name = 'production.worker.entry'
    _description = 'Production Worker Entry'
    _order = 'date desc'

    date = fields.Date('Date', default=fields.Date.today, required=True)
    output_qty = fields.Integer('Output Quantity', required=True)
    note = fields.Text('Note')
    
    # Relationships
    employee_id = fields.Many2one('hr.employee', string='Worker', required=True)
    bundle_id = fields.Many2one('production.bundle', string='Bundle', required=True)
    operation_id = fields.Many2one('operation.price', string='Operation', required=True) 