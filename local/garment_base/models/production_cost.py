from odoo import models, fields, api

class ProductionCost(models.Model):
    _name = 'production.cost'
    _description = 'Production Cost'

    cost_type = fields.Selection([
        ('export_tax', 'Export Tax'),
        ('vat', 'VAT'),
        ('water', 'Water'),
        ('bonded', 'Bonded'),
        ('utilities', 'Utilities'),
        ('misc_fees', 'Misc Fees'),
        ('shipping', 'Shipping'),
        ('management', 'Management'),
        ('transport', 'Transport'),
        ('other', 'Other'),
        # Temporary values to allow cleanup of invalid records
        ('total_other_cost', 'Total Other Cost (Invalid)'),
        ('material_cost', 'Material Cost (Invalid)'),
        ('process_cost', 'Process Cost (Invalid)'),
    ], string='Cost Type', required=True)
    
    amount = fields.Float('Amount', digits=(12, 2))
    note = fields.Text('Note')
    
    # Relationships
    order_id = fields.Many2one('production.order', string='Production Order', required=True, ondelete='cascade') 
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        return result
    
    def write(self, vals):
        result = super().write(vals)
        return result
    
    def unlink(self):
        result = super().unlink()
        return result 