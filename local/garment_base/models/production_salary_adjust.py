from odoo import models, fields, api

class ProductionSalaryAdjust(models.Model):
    _name = 'production.salary.adjust'
    _description = 'Production Salary Adjustment'

    month = fields.Date('Month', required=True)
    old_amount = fields.Float('Old Amount', digits=(16, 2), required=True)
    new_amount = fields.Float('New Amount', digits=(16, 2), required=True)
    reason = fields.Text('Reason')
    
    # Relationships
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True) 