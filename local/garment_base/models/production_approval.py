from odoo import models, fields, api

class ProductionApproval(models.Model):
    _name = 'production.approval'
    _description = 'Production Approval'

    approved = fields.Boolean('Approved', default=False)
    approval_date = fields.Date('Approval Date')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    
    @api.onchange('approved')
    def _onchange_approved(self):
        if self.approved and not self.approval_date:
            self.approval_date = fields.Date.today() 