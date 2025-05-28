from odoo import models, fields, api

class ApprovalRequest(models.Model):
    _name = 'approval.request'
    _description = 'Approval Request'
    _order = 'approval_date desc'

    order_id = fields.Many2one('production.order', string='Production Order', required=True)
    approver = fields.Char('Approver', required=True)
    approved = fields.Boolean('Approved', default=False)
    approval_date = fields.Date('Approval Date')