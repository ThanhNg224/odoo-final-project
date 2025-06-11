from odoo import models, fields, api

class ProductionOrderLine(models.Model):
    _name = 'production.order.line'
    _description = 'Production Order Line'

    size = fields.Char('Size', required=True)
    planned_qty = fields.Integer('Planned Quantity', required=True)
    done_qty = fields.Integer('Done Quantity', compute='_compute_done_qty', store=True)
    progress = fields.Float('Progress %', compute='_compute_progress', store=True)
    completion_status = fields.Char('Status', compute='_compute_completion_status')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade')
    bundle_ids = fields.One2many('production.bundle', 'order_line_id', string='Bundles')
    sample_id = fields.Many2one('garment.sample', string='Sample', related='order_id.sample_id', store=True, readonly=True)
    
    # Related fields from sample
    sample_name = fields.Char(related='sample_id.name', string='Sample Name', readonly=True)
    client = fields.Char(related='order_id.client', string='Client', readonly=True)
    color = fields.Char('Color')
    
    @api.depends('bundle_ids.is_completed', 'bundle_ids.qty')
    def _compute_done_qty(self):
        for line in self:
            # Calculate done quantity based on completed bundles
            completed_bundles = line.bundle_ids.filtered('is_completed')
            line.done_qty = sum(bundle.qty for bundle in completed_bundles)
    
    @api.depends('done_qty', 'planned_qty')
    def _compute_progress(self):
        for line in self:
            if line.planned_qty > 0:
                line.progress = (line.done_qty / line.planned_qty) * 100
            else:
                line.progress = 0
    
    @api.depends('progress')
    def _compute_completion_status(self):
        for line in self:
            if line.progress >= 100:
                line.completion_status = 'Completed'
            elif line.progress > 0:
                line.completion_status = 'In Progress'
            else:
                line.completion_status = 'Not Started'
    
    def name_get(self):
        result = []
        for line in self:
            status_icon = "✓" if line.progress >= 100 else "⏳" if line.progress > 0 else "⭕"
            name = f"{line.order_id.name} - {line.size} ({line.done_qty}/{line.planned_qty}) {status_icon}"
            result.append((line.id, name))
        return result