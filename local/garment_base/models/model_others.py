from odoo import models, fields

class InventoryColor(models.Model):
    _name = 'garment.inventory.color'
    _description = 'Inventory Color'

    code = fields.Char(string='Color Code')
    name = fields.Char(string='Color')


class InventoryMaterial(models.Model):
    _name = 'garment.inventory.material'
    _description = 'Inventory Material'

    code = fields.Char(string='Material Code')
    name = fields.Char(string='Material Name')

class Department(models.Model):
    _name = 'garment.department'
    _description = 'Department'

    name = fields.Char(string='Department Name', required=True)
    supervisor = fields.Char(string='Supervisor')