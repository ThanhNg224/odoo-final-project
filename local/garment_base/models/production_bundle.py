from odoo import models, fields, api

class ProductionBundle(models.Model):
    _name = 'production.bundle'
    _description = 'Production Bundle'

    bundle_no = fields.Char('Bundle Number', required=True, unique=True)
    size = fields.Char('Size', required=True)
    qty = fields.Integer('Quantity', required=True)
    ticket_printed = fields.Boolean('Ticket Printed', default=False)
    is_completed = fields.Boolean('Completed', default=False, help="Check this when the bundle is completed")
    completion_date = fields.Datetime('Completion Date', readonly=True)
    
    # Relationships
    order_line_id = fields.Many2one('production.order.line', string='Order Line', required=True, ondelete='cascade')
    order_id = fields.Many2one('production.order', related='order_line_id.order_id', string='Production Order', store=True, readonly=True)
    
    # Related fields for display
    sample_name = fields.Char(related='order_id.sample_name', string='Sample Name', readonly=True)
    client = fields.Char(related='order_id.client', string='Client', readonly=True)
    
    # ADD THESE METHODS:
    def action_view_qr_ticket(self):
        """View QR ticket in browser"""
        self.ensure_one()
        try:
            action = self.env.ref('garment_production.action_bundle_qr_report_html')
            return action.report_action(self)
        except Exception as e:
            # Fallback if the report doesn't exist
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'QR Report Not Found',
                    'message': f'QR report template not found: {str(e)}',
                    'type': 'warning',
                }
            }

    def action_download_qr_ticket(self):
        """Download QR ticket as PDF"""
        self.ensure_one()
        try:
            action = self.env.ref('garment_production.action_bundle_qr_report')
            return action.report_action(self)
        except Exception as e:
            # Fallback if the report doesn't exist
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'QR Report Not Found',
                    'message': f'QR report template not found: {str(e)}',
                    'type': 'warning',
                }
            }

    @api.onchange('is_completed')
    def _onchange_is_completed(self):
        """Update completion date when bundle is marked as completed"""
        if self.is_completed:
            self.completion_date = fields.Datetime.now()
        else:
            self.completion_date = False
    
    def name_get(self):
        result = []
        for bundle in self:
            name = f"{bundle.bundle_no} - {bundle.size} ({bundle.qty} pcs)"
            if bundle.is_completed:
                name += " ✓"
            result.append((bundle.id, name))
        return result
    
    def toggle_completion(self):
        """Toggle completion status of the bundle"""
        for bundle in self:
            bundle.is_completed = not bundle.is_completed
            if bundle.is_completed:
                bundle.completion_date = fields.Datetime.now()
            else:
                bundle.completion_date = False