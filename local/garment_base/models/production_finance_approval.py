from odoo import models, fields, api

class ProductionFinanceApproval(models.Model):
    _name = 'production.finance.approval'
    _description = 'Production Finance Approval'

    amount = fields.Float('Amount', digits=(16, 2), required=True)
    approved = fields.Boolean('Approved', default=False)
    date = fields.Date('Approval Date')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    
    @api.onchange('approved')
    def _onchange_approved(self):
        if self.approved and not self.date:
            self.date = fields.Date.today() 