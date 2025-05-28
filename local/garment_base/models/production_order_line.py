from odoo import models, fields, api

class ProductionOrderLine(models.Model):
    _name = 'production.order.line'
    _description = 'Production Order Line'

    size = fields.Char('Size', required=True)
    planned_qty = fields.Integer('Planned Quantity', required=True)
    done_qty = fields.Integer('Done Quantity', default=0)
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    bundle_ids = fields.One2many('production.bundle', 'order_line_id', string='Bundles')
    sample_id = fields.Many2one('garment.sample', string='Sample', related='order_id.sample_id', store=True, readonly=True)
    
    # Related fields from sample
    sample_name = fields.Char(related='sample_id.name', string='Sample Name', readonly=True)
    client = fields.Char(related='sample_id.client', string='Client', readonly=True)
    color = fields.Char('Color')
    
    @api.depends('bundle_ids.qty')
    def _compute_done_qty(self):
        for line in self:
            line.done_qty = sum(bundle.qty for bundle in line.bundle_ids) 