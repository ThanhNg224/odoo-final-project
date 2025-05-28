from odoo.exceptions import ValidationError
from odoo import models, fields, api
import json

class SpecificationDetail(models.Model):
    _name = 'garment.specification_detail'
    _description = 'Specification Detail'

    name = fields.Char(string='Name')
    template = fields.Json(string='Template', default=lambda self: [
        ["Color", "XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL"],
        ['', 0, 0, 0, 0, 0, 0, 0, 0],
    ])

    @api.model
    def create(self, vals):
        if self.env['garment.specification_detail'].search([('name', '=', vals.get('name'))]):
            raise ValidationError('Name already exists')
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().write(vals)

class FinishedProductSize(models.Model):
    _name = 'garment.finished_product_size'
    _description = 'Finished Product Size'

    name = fields.Char(string='Name')
    template = fields.Json(string='Template', default=lambda self: [['', ''], ['', '']])

    @api.model
    def create(self, vals):
        if self.env['garment.finished_product_size'].search([('name', '=', vals.get('name'))]):
            raise ValidationError('Name already exists')
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().write(vals)

class MaterialDetail(models.Model):
    _name = 'garment.material_detail'
    _description = 'Material Detail'

    name = fields.Char(string='Template Name')
    template = fields.Json(string='Template', default=lambda self: [
        ["Material Name", "Material Code", "Color", "Color Code", "Specification", "Unit", "Part", "Quantity per Unit", "Loss per Unit", "Unit Quantity", "Total Quantity Used", "Unit Price", "Supplier"],
        ["", "", "", "", "", "", "", 0, 0, 0, 0, 0, ""]
    ])

    @api.model
    def create(self, vals):
        if 'template' in vals:
            if isinstance(vals['template'], str):
                try:
                    vals['template'] = json.loads(vals['template'])
                except Exception:
                    pass
            elif isinstance(vals['template'], list):
                vals['template'] = vals['template']
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals:
            if isinstance(vals['template'], str):
                try:
                    vals['template'] = json.loads(vals['template'])
                except Exception:
                    pass
            elif isinstance(vals['template'], list):
                vals['template'] = vals['template']
        return super().write(vals)

class OtherCost(models.Model):
    _name = 'garment.other_cost'
    _description = 'Other Costs'

    name = fields.Char(string='Name')
    template = fields.Json(string='Template', default=lambda self: [{"cost_name": "", "amount": 0}])

    @api.model
    def create(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().write(vals)

class ProcessTable(models.Model):
    _name = 'garment.process_table'
    _description = 'Process Table'

    name = fields.Char(string='Name')
    template = fields.Json(string='Template', default=lambda self: [{"name": "", "unit_price": 0, "multiplier": 1, "notes": ""}])

    @api.model
    def create(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().write(vals)

class ProgressTemplate(models.Model):
    _name = 'garment.progress_template'
    _description = 'Progress Template'

    name = fields.Char(string='Name')
    template = fields.Json(string='Template', default=lambda self: 
        [{"name": "Unnamed", "state": "not_started", 
          "plan":{"start_date": "", "end_date": "", "quantity": 0, "person_in_charge": ""},
          "actual":{"start_date": "", "end_date": "", "total_quantity": 0, "person_in_charge": "", "completed_quantity": 0, "defect_quantity": 0, "department_id": "", "unit_price": 0},
          "remark": ""}])

    @api.model
    def create(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().create(vals)
    
    @api.model
    def write(self, vals):
        if 'template' in vals and isinstance(vals['template'], str):
            try:
                vals['template'] = json.loads(vals['template'])
            except Exception:
                pass
        return super().write(vals)