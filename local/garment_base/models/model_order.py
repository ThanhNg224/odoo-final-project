# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import json
import io
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from odoo.tools.misc import file_path


class GarmentOrder(models.Model):
    _name = 'garment.order'
    _description = 'Garment Order'

    name = fields.Char(string="Order Name", required=True)
    code = fields.Char(string='Order Code', readonly=True, copy=False, default=lambda self: self._generate_order_code())
    shape = fields.Char(string='Shape')
    color = fields.Char(string="Color")
    quantity = fields.Integer(string="Unit Quantity", required=True)
    unit_price = fields.Float(string="Unit Price", required=True)
    cutting_date = fields.Date(string="Cutting Date")
    issuing_company = fields.Char(string="Issuing Company")
    receiving_company = fields.Char(string="Receiving Company")
    issuing_company_phone = fields.Char(string="Issuing Company Phone")
    receiving_company_phone = fields.Char(string="Receiving Company Phone")
    issuing_date = fields.Date(string="Issuing Date") # Ngày doanh nghiệp phát hành đơn
    receiving_date = fields.Date(string="Receiving Date") # Ngày doanh nghiệp nhận đơn
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('new', 'New development'),
        ('in_progress', 'Can be produced'),
        ('eliminated', 'Eliminated')
    ], string="Status", default='new')

    sample_ids = fields.Many2many('garment.sample', 'garment_order_sample_rel', 'order_id', 'sample_id', string='Samples', domain=[('state', '=', 'in_progress')])
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

    material_issuance_ids = fields.One2many(
        'garment.receipt.line',
        compute='_compute_material_issuance_ids',
        string='Related Material Issuances'
    )

    remark = fields.Html(string='Remarks')
    image_detail = fields.Binary(string='Image Details', attachment=True)
    related_document = fields.Binary(string='Related Documents', attachment=True)
    is_stored = fields.Boolean(string='Is Stored', default=False)
    is_waiting_for_approval = fields.Boolean(string='Is Waiting for Approval', default=False)

    def _generate_order_code(self):
        # Get the next sequence number
        return self.env['ir.sequence'].next_by_code('garment.order') or '/'
    
    @api.depends()
    def _compute_material_issuance_ids(self):
        for record in self:
            # Find all material receipt lines where item_type='order' and item_id matches this order's ID
            material_lines = self.env['garment.receipt.line'].search([
                ('from_type', '=', 'order'),
                ('item_type', '=', 'material'),
                ('item_id', '=', str(record.id))
            ])
            record.material_issuance_ids = material_lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self._generate_order_code()
        return super().create(vals_list)
    
    def action_mark_ready_for_production(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        return True

    def action_mark_discontinued(self):
        self.ensure_one()
        self.write({'state': 'eliminated'})
        return True

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
            'res_model': 'garment.order',
            'view_mode': 'tree,form',
            'target': 'main',
            'flags': {'mode': 'list'},
            'context': {
                'form_view_ref': 'garment_order.view_garment_order_form_view',
                'create_view_ref': 'garment_order.view_garment_order_form_edit'
            }
        }
    
    def action_stock_in(self):
        self.ensure_one()
        
        # Create inventory receipt line
        if self.is_stored:
            raise ValidationError(_("Order is already in stock."))
        self.env['garment.receipt.line'].create({
            'type': 'in',
            'item_type': 'order',
            'item_id': str(self.id),
            'remark': f"Order details: Shape: {self.shape}, Color: {self.color}, Quantity: {self.quantity}"
        })
        self.write({'is_waiting_for_approval': True})

        # Show success notification using Odoo's bus notification system
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': _('Success'),
                'message': _('Stock in order "%s" request has been successfully sent.') % self.name,
                'type': 'success',
                'sticky': False,
                'fadeout': 2000,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Garment Orders'),
            'res_model': 'garment.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_order.view_garment_order_tree').id, 'tree'),
                (self.env.ref('garment_order.view_garment_order_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('is_stored', '=', False)],
            'context': {
                'form_view_ref': 'garment_order.view_garment_order_form_view',
                'create_view_ref': 'garment_order.view_garment_order_form_edit',
                'tree_view_ref': 'garment_order.view_garment_order_tree'
            },
        }

    def action_stock_out(self):
        self.ensure_one()
        if not self.is_stored:
            raise ValidationError(_("Order is not in stock."))
        # Create inventory receipt line
        self.env['garment.receipt.line'].create({
            'type': 'out',
            'item_type': 'order',
            'item_id': str(self.id),
            'remark': f"Order details: Shape: {self.shape}, Color: {self.color}, Quantity: {self.quantity}"
        })
        self.write({'is_waiting_for_approval': True})

        # Show success notification using Odoo's bus notification system
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': _('Success'),
                'message': _('Stock out order "%s" request has been successfully sent.') % self.name,
                'type': 'success',
                'sticky': False,
                'fadeout': 2000,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stored Orders'),
            'res_model': 'garment.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_order.view_garment_order_tree').id, 'tree'),
                (self.env.ref('garment_order.view_garment_order_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('is_stored', '=', True)],
            'context': {
                'tree_view_ref': 'garment_order.view_garment_order_tree',
                'form_view_ref': 'garment_order.view_garment_order_form_view'
            },
        }

    def action_export_pdf(self):
        self.ensure_one()
        self._register_fonts()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='VN', fontName='TimesNewRoman', fontSize=12))
        styles.add(ParagraphStyle(name='VN-Bold', fontName='TimesNewRoman-Bold', fontSize=12))
        styles.add(ParagraphStyle(name='VN-Title', fontName='TimesNewRoman-Bold', fontSize=16, alignment=1))
        elements = []

        # Title
        title = Paragraph('<b>ORDER FORM</b>', styles['VN-Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Customer Info
        customer_info = [
            [Paragraph(_('Customer:'), styles['VN']), self.issuing_company or ''],
            [Paragraph(_('Contact Person:'), styles['VN']), self.published_by.name or ''],
            [Paragraph(_('Phone Number:'), styles['VN']), self.issuing_company_phone or ''],
            [Paragraph(_('Delivery Address:'), styles['VN']), self.receiving_company or ''],
            [Paragraph(_('Order Code:'), styles['VN']), self.code or ''],
            [Paragraph(_('Order Date:'), styles['VN']), str(self.issuing_date) if self.issuing_date else ''],
            [Paragraph(_('Expected Delivery Date:'), styles['VN']), str(self.receiving_date) if self.receiving_date else ''],
            [Paragraph(_('Responsible Staff:'), styles['VN']), self.published_by.name or ''],
        ]
        for row in customer_info:
            elements.append(Table([row], colWidths=[220, 320], style=TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'TimesNewRoman'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (1, -1), 42),
            ])))
        elements.append(Spacer(1, 8))

        # Product Table
        product_table_data = [
            [_('No.'), _('Sample Code'), _('Sample Name'), _('Size'), _('Color'), _('Quantity'), _('Unit Price' + '(' + self.currency_id.name + ')')]
        ]
        for idx, sample in enumerate(self.sample_ids, 1):
            print(sample.total_price)
            product_table_data.append([
                str(idx),
                sample.code or '',
                sample.name or '',
                sample.pattern_size or '',
                sample.color or '',
                str(sample.quantity or ''),
                f"{sample.total_price:,.0f}" if hasattr(sample, 'total_price') else ''
            ])
        product_table = Table(product_table_data, colWidths=[30, 70, 120, 70, 60, 60, 100])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'TimesNewRoman-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(Paragraph(_('Product List:'), styles['VN']))
        elements.append(Spacer(1, 6))
        elements.append(product_table)
        elements.append(Spacer(1, 16))

        # Note
        note = self.remark or _('')
        elements.append(Paragraph(_('Note:'), styles['VN']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(note.replace('\n', '<br/>'), styles['VN']))
        elements.append(Spacer(1, 16))

        elements.append(Paragraph(f'{_("Prepared By")}: ____________________________________________', styles['VN']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f'{_("Approved By")}: ____________________________________________', styles['VN']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f'{_("Customer Confirmation")}: _______________', styles['VN']))
        elements.append(Spacer(1, 10))

        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        filename = f"order_form_{self.code}_{fields.Date.today()}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    @api.model
    def _register_fonts(self):
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        pdfmetrics.registerFont(TTFont('TimesNewRoman', file_path('garment_base/static/fonts/SVN-Times New Roman.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', file_path('garment_base/static/fonts/SVN-Times New Roman Bold.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', file_path('garment_base/static/fonts/SVN-Times New Roman Italic.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-BoldItalic', file_path('garment_base/static/fonts/SVN-Times New Roman Bold Italic.ttf')))
