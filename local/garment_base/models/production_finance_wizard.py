from odoo import models, fields, api

class ProductionFinanceWizard(models.TransientModel):
    _name = 'production.finance.wizard'
    _description = 'Update Finance Status'
    
    # Add this line to bypass security for this model
    _check_company_auto = True
    
    order_id = fields.Many2one('production.order', string='Production Order', required=True)
    finance_state = fields.Selection([
        ('waiting', 'Waiting Payment'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid')
    ], string='Finance Status', required=True)
    
    payment_amount = fields.Float('Payment Received', help="Total amount received from customer")
    payment_notes = fields.Text('Payment Notes', help="Notes about payments")
    
    # Display current info
    current_finance_state = fields.Selection(related='order_id.finance_state', string='Current Status', readonly=True)
    current_payment = fields.Float(related='order_id.payment_amount', string='Current Payment', readonly=True)
    order_total = fields.Float(related='order_id.cost_total', string='Order Total', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        if 'order_id' in self.env.context:
            order_id = self.env.context['order_id']
            order = self.env['production.order'].browse(order_id)
            result.update({
                'order_id': order_id,
                'finance_state': order.finance_state,
                'payment_amount': order.payment_amount,
                'payment_notes': order.payment_notes,
            })
        return result
    
    def action_update_finance(self):
        """Update finance status"""
        self.order_id.write({
            'finance_state': self.finance_state,
            'payment_amount': self.payment_amount,
            'payment_notes': self.payment_notes,
            'finance_approved_by': self.env.user if self.finance_state != 'waiting' else False,
            'finance_approval_date': fields.Datetime.now() if self.finance_state != 'waiting' else False,
        })
        
        return {'type': 'ir.actions.act_window_close'}