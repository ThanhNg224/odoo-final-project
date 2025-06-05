# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64
import json
import io
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class GarmentOrder(models.Model):
    _name = 'garment.order'
    _description = 'Garment Order'

    name = fields.Char(string="Order Name", required=True)
    order_number = fields.Char(string="Order Number", required=True)
    shape = fields.Char(string='Shape')
    color = fields.Char(string="Color")
    quantity = fields.Integer(string="Unit Quantity", required=True)
    unit_price = fields.Float(string="Unit Price", required=True)
    cutting_date = fields.Date(string="Cutting Date")
    issuing_company = fields.Char(string="Issuing Company")
    receiving_company = fields.Char(string="Receiving Company")
    issuing_company_phone = fields.Char(string="Phone Number")
    receiving_company_phone = fields.Char(string="Phone Number")
    issuing_date = fields.Date(string="Issuing Date") # Ngày doanh nghiệp phát hành đơn
    receiving_date = fields.Date(string="Receiving Date") # Ngày doanh nghiệp nhận đơn
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft')

    sample_ids = fields.Many2many('garment.sample', 'garment_order_sample_rel', 'order_id', 'sample_id', string='Samples')
    # production_id = fields.Many2one('garment.production', string="Related Production")
    department_id = fields.Many2one('garment.department', string='Department')
    published_by = fields.Many2one('res.users', string='Published By', default=lambda self: self.env.user)
    progress_detail = fields.Json(string='Progress Detail', default=lambda self: [])
    material_detail = fields.Json(string='Material Detail', default=lambda self: [
        ["Material Name", "Material Code", "Color", "Color Code", "Specification", "Unit", "Part", "Quantity per Unit", "Loss per Unit", "Unit Quantity", "Total Quantity Used", "Unit Price", "Supplier"],
        ["", "", "", "", "", "", "", 0, 0, 0, 0, 0, ""]
    ])
    other_cost = fields.Json(string='Other Costs', default=lambda self: [])
    specification_detail = fields.Json(string='Specification Detail', default=lambda self: [
        ["Color", "XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL"],
        ['', 0, 0, 0, 0, 0, 0, 0, 0],
    ])

    remark = fields.Html(string='Remarks')
    image_detail = fields.Binary(string='Image Details', attachment=True)
    related_document = fields.Binary(string='Related Documents', attachment=True)

    def action_open_edit_form(self):
        self.ensure_one()
        return {
            'name': 'Edit Order',
            'type': 'ir.actions.act_window',
            'res_model': 'garment.order',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('garment_order.view_garment_order_form_edit').id,
            'target': 'new',
            'flags': {'form': {'action_buttons': True}},
            'context': {'form_view_ref': 'garment_order.view_garment_order_form_edit'},
        }

    def action_delete_record(self):
        self.ensure_one()
        action = self.env.ref('garment_order.action_garment_order').read()[0]
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': action['name'],
            'res_model': 'garment.sample',
            'view_mode': 'tree,form',
            'target': 'main',
            'flags': {'mode': 'list'},
            'context': {
                'form_view_ref': 'garment_sample.view_garment_sample_form_view',
                'create_view_ref': 'garment_sample.view_garment_sample_form_edit'
            }
        }