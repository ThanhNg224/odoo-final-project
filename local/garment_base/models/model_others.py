from odoo import models, fields

class SampleImage(models.Model):
    _name = 'garment.sample.image'
    _description = 'Sample Image'

    image = fields.Binary(string='Image', required=True)
    sample_id = fields.Many2one('garment.sample', string='Sample', required=True, ondelete='cascade')

class Department(models.Model):
    _name = 'garment.department'
    _description = 'Department'

    name = fields.Char(string='Department Name', required=True)
    supervisor = fields.Char(string='Supervisor')