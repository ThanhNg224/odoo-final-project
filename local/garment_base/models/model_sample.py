import base64
import os
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from odoo.modules.module import get_module_resource
import json
import io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import TTFSearchPath
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from odoo.tools.misc import file_path

class Sample(models.Model):
    _name = 'garment.sample'
    _description = 'Garment Sample'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Sample Code', copy=False, default=lambda self: self._generate_sample_code())
    shape = fields.Char(string='Shape')
    color = fields.Char(string='Color')
    brand = fields.Char(string='Brand')
    client = fields.Char(string='Client')
    quotation = fields.Float(string='Budget Quotation')
    actual_quotation = fields.Float(string='Actual Quotation')
    designer = fields.Char(string='Designer')
    phone_number = fields.Char(string='Phone Number')
    pattern_maker = fields.Char(string='Pattern Maker')
    pattern_drafter = fields.Char(string='Pattern Drafter')
    quantity = fields.Integer(string='Quantity')
    pattern_size = fields.Char(string='Pattern Size')
    development_date = fields.Date(string='Development Date', default=fields.Date.today)
    update_date = fields.Date(string='Update At', default=fields.Date.today, readonly=True)

    finished_product_size = fields.Json(string='Finished Product Size', default=lambda self: [['', ''], ['', '']])
    material_detail = fields.Json(string='Material Detail', default=lambda self: [
        ["Material Name", "Material Code", "Color", "Color Code", "Specification", "Unit", "Part", "Quantity per Unit", "Loss per Unit", "Unit Quantity", "Total Quantity Used", "Unit Price", "Supplier"],
        ["", "", "", "", "", "", "", 0, 0, 0, 0, 0, ""]
    ])
    material_detail_initial_cost = fields.Float(string='Material Detail Initial Cost')
    process_table = fields.Json(string='Process Table', default=lambda self: [])
    other_cost = fields.Json(string='Other Costs', default=lambda self: [])

    progress_detail = fields.Json(string='Progress Detail', default=lambda self: [])
    technical_requirements = fields.Html(string='Technical Requirements')
    remark = fields.Html(string='Remarks')
    state = fields.Selection([
        ('new', 'New development'),
        ('in_progress', 'Can be produced'),
        ('eliminated', 'Eliminated')
    ], string="Status", default='new')

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    department_id = fields.Many2one('garment.department', string='Department')
    published_by = fields.Many2one('res.users', string='Published By', default=lambda self: self.env.user)
    image_details = fields.Many2many(comodel_name='ir.attachment', string="Image Details", 
        relation='garment_sample_image_detail_rel',
        column1='sample_id',
        column2='image_id')
    related_document = fields.Binary(string='Related Documents', attachment=True)
    is_stored = fields.Boolean(string='Is Stored', default=False)
    is_waiting_for_approval = fields.Boolean(string='Is Waiting for Approval', default=False)

    order_ids = fields.Many2many('garment.order', 'garment_order_sample_rel', 'sample_id', 'order_id', string='Related Orders')
    production_ids = fields.One2many('production.order', 'sample_id', string='Related Productions')
    material_issuance_ids = fields.One2many(
        'garment.receipt.line',
        compute='_compute_material_issuance_ids',
        string='Related Material Issuances'
    )
    all_samples = fields.Many2many('garment.sample', compute='_compute_all_samples', string="All Samples")
    total_price = fields.Float(string='Total Price', compute='_compute_total_price')

    @api.depends()
    def _compute_material_issuance_ids(self):
        for record in self:
            # Find all material receipt lines where item_type='sample' and item_id matches this sample's ID
            material_lines = self.env['garment.receipt.line'].search([
                ('from_type', '=', 'sample'),
                ('item_type', '=', 'material'),
                ('item_id', '=', str(record.id))
            ])
            record.material_issuance_ids = material_lines

    @api.depends('material_detail', 'process_table', 'other_cost')
    def _compute_total_price(self):
        for record in self:
            # Calculate material cost
            material_cost = 0
            if record.material_detail and len(record.material_detail) > 1:
                for row in record.material_detail[1:]:  # Skip header row
                    if len(row) >= 12:  # Ensure row has enough columns
                        total_quantity_used = float(row[10] or 0)  # Total Quantity Used
                        unit_price = float(row[11] or 0)  # Unit Price
                        material_cost += total_quantity_used * unit_price

            # Calculate process cost
            process_cost = 0
            if record.process_table and isinstance(record.process_table, list):
                for item in record.process_table:
                    if isinstance(item, dict):
                        process_cost += item.get('unit_price', 0) * item.get('multiplier', 1)

            # Calculate other cost
            other_cost = 0
            if record.other_cost and isinstance(record.other_cost, list):
                for item in record.other_cost:
                    if isinstance(item, dict):
                        other_cost += item.get('amount', 0)

            # Set total price as sum of all costs
            record.total_price = material_cost + process_cost + other_cost

    @api.depends()
    def _compute_all_samples(self):
        for record in self:
            record.all_samples = self.env['garment.sample'].search([])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self._generate_sample_code()
                vals['actual_quotation'] = vals['quotation']
            
        return super().create(vals_list)

    def write(self, vals):
        for key in ['finished_product_size', 'material_detail', 'process_table', 'other_cost']:
            if key in vals and isinstance(vals[key], str):
                try:
                    vals[key] = json.loads(vals[key])
                except Exception:
                    pass
        vals['update_date'] = fields.Date.today()

        return super().write(vals)

    def action_open_edit_form(self):
        self.ensure_one()
        return {
            'name': 'Edit Sample',
            'type': 'ir.actions.act_window',
            'res_model': 'garment.sample',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('garment_sample.view_garment_sample_form_edit').id,
            'target': 'new',
            'flags': {'form': {'action_buttons': True}},
            'context': {'form_view_ref': 'garment_sample.view_garment_sample_form_edit'},
        }

    def action_stock_in(self):
        self.ensure_one()
        
        print("before: " + str(self.is_stored) + " " + str(self.is_waiting_for_approval) + " " + str(self.id))
        # Create inventory receipt line
        if self.is_stored:
            raise ValidationError(_("Sample is already in stock."))
        self.env['garment.receipt.line'].create({
            'type': 'in',
            'item_type': 'sample',
            'item_id': str(self.id),
            'remark': f"Sample details: Shape: {self.shape}, Color: {self.color}, Brand: {self.brand}"
        })
        self.write({'is_waiting_for_approval': True})

        # Show success notification using Odoo's bus notification system
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': _('Success'),
                'message': _('Stock in sample "%s" request has been successfully sent.') % self.name,
                'type': 'success',
                'sticky': False,
                'fadeout': 2000,
            }
        )
        print(str(self.is_stored) + " " + str(self.is_waiting_for_approval) + " " + str(self.id))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Garment Samples'),
            'res_model': 'garment.sample',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_sample.view_garment_sample_tree').id, 'tree'),
                (self.env.ref('garment_sample.view_garment_sample_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('is_stored', '=', False)],
            'context': {
                'form_view_ref': 'garment_sample.view_garment_sample_form_view',
                'create_view_ref': 'garment_sample.view_garment_sample_form_edit',
                'tree_view_ref': 'garment_sample.view_garment_sample_tree'
            },
        }

    def action_stock_out(self):
        self.ensure_one()
        if not self.is_stored:
            raise ValidationError(_("Sample is not in stock."))
        # Create inventory receipt line
        self.env['garment.receipt.line'].create({
            'type': 'out',
            'item_type': 'sample',
            'item_id': str(self.id),
            'remark': f"Sample details: Shape: {self.shape}, Color: {self.color}, Brand: {self.brand}"
        })
        self.write({'is_waiting_for_approval': True})

        # Show success notification using Odoo's bus notification system
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': _('Success'),
                'message': _('Stock out sample "%s" request has been successfully sent.') % self.name,
                'type': 'success',
                'sticky': False,
                'fadeout': 2000,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stored Samples'),
            'res_model': 'garment.sample',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('garment_inventory.view_stored_sample_tree').id, 'tree'),
                (self.env.ref('garment_inventory.view_stored_sample_form_view').id, 'form')
            ],
            'target': 'main',
            'domain': [('is_stored', '=', True)],
            'context': {
                'tree_view_ref': 'garment_inventory.view_stored_sample_tree',
                'form_view_ref': 'garment_inventory.view_stored_sample_form_view'
            },
        }

    def action_mark_ready_for_production(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        return True

    def action_mark_discontinued(self):
        self.ensure_one()
        self.write({'state': 'eliminated'})
        return True

    def action_delete_record(self):
        self.ensure_one()
        action = self.env.ref('garment_sample.action_garment_sample').read()[0]
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

    def unlink(self):
        for record in self:
            # Get all attachment IDs related to this sample
            attachment_ids = self.env['ir.attachment'].search([
                '|',
                ('res_model', '=', self._name),
                ('res_id', '=', record.id),
                ('res_model', '=', self._name),
                ('res_id', 'in', record.image_details.ids)
            ]).ids

            # Delete directly from ir.attachment table
            if attachment_ids:
                self.env.cr.execute("DELETE FROM ir_attachment WHERE id IN %s", (tuple(attachment_ids),))

            # Delete the sample record from database
            self.env.cr.execute("DELETE FROM garment_sample WHERE id = %s", (record.id,))
            self.env.cr.execute("DELETE FROM garment_sample_image_detail_rel WHERE sample_id = %s", (record.id,))
            
        return True

    def action_save(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Garment Samples',
            'res_model': 'garment.sample',
            'view_mode': 'tree,form',
            'target': 'main',
            'flags': {'mode': 'list'},
            'context': {
                'form_view_ref': 'garment_sample.view_garment_sample_form_view',
                'create_view_ref': 'garment_sample.view_garment_sample_form_edit'
            }
        }
    
    @api.model
    def _register_fonts(self):
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        pdfmetrics.registerFont(TTFont('TimesNewRoman', file_path('garment_base/static/fonts/SVN-Times New Roman.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', file_path('garment_base/static/fonts/SVN-Times New Roman Bold.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', file_path('garment_base/static/fonts/SVN-Times New Roman Italic.ttf')))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-BoldItalic', file_path('garment_base/static/fonts/SVN-Times New Roman Bold Italic.ttf')))

    def _get_season(self, date):
        """Determine the season based on the given date.
        Spring: March to May
        Summer: June to August
        Fall: September to November
        Winter: December to February
        """
        if not date:
            return ''
            
        month = date.month
        year = date.year
        
        if 3 <= month <= 5:
            season = _('Spring')
        elif 6 <= month <= 8:
            season = _('Summer')
        elif 9 <= month <= 11:
            season = _('Fall')
        else:
            season = _('Winter')
            
        return f"{season} {year}"

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
        title = Paragraph(f'<b>{_("SAMPLE DESIGN APPROVAL FORM")}</b>', styles['VN-Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        status_labels = {
            'new': _('New Development'),
            'in_progress': _('Ready for Production'),
            'eliminated': _('Eliminated'),
        }

        header_data = [
            [f"{_('Sample Code')}: {self.code or ''}",              f"{_('Sample Name')}: {self.name or ''}"],
            [f"{_('Designer')}: {self.designer or ''}",  f"{_('Creation Date')}: {self.development_date or ''}"],
            [f"{_('Product Type')}: {self.shape or ''}",     f"{_('Season')}: {self._get_season(self.development_date)}"],
            [f"{_('Size')}: {self.pattern_size or ''}",       f"{_('Color')}: {self.color or ''}"],
            [f"{_('Status')}: {status_labels.get(self.state, '')}", ""],
        ]
        tbl = Table(header_data, colWidths=[270, 270])
        tbl.setStyle(TableStyle([
            ('FONTNAME',     (0, 0), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE',     (0, 0), (-1, -1), 11),
            ('ALIGN',        (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 10))

        # Technical Information
        elements.append(Paragraph(f'<b>{_("Technical Information")}:</b>', styles['VN']))
        elements.append(Spacer(1, 6))

        material_detail = self.material_detail or []

        # --- Process material_detail to create tech_table_data ---
        material_header = material_detail[0] if material_detail else []
        
        # Find column indices
        name_idx = material_header.index(_('Material Name')) if _('Material Name') in material_header else None
        spec_idx = material_header.index(_('Specification')) if _('Specification') in material_header else None
        note_idx = material_header.index(_('Note')) if _('Note') in material_header else None

        # Initialize table header
        tech_table_data = [
            [_('No.'), _('Category'), _('Description'), _('Note')]
        ]

        # Process each row from material_detail (skip header row)
        for i, row in enumerate(material_detail[1:], start=1):
            if not isinstance(row, list):
                continue
                
            # Get complete strings for each field
            category = str(row[name_idx]) if name_idx is not None and len(row) > name_idx else ''
            description = str(row[spec_idx]) if spec_idx is not None and len(row) > spec_idx else ''
            note = str(row[note_idx]) if note_idx is not None and len(row) > note_idx else ''
            
            # Add row if any field has data
            if any([category, description, note]):
                tech_table_data.append([str(i), category, description, note])

        # Tạo Table và style như cũ
        tech_tbl = Table(tech_table_data, colWidths=[40, 100, 300, 100])
        tech_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME',   (0, 0), (-1, 0), 'TimesNewRoman-Bold'),
            ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE',   (0, 0), (-1, 0), 11),
            ('GRID',       (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME',   (0, 1), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE',   (0, 1), (-1, -1), 10),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tech_tbl)
        elements.append(Spacer(1, 16))

        # Approval section
        elements.append(Paragraph(f'{_("Approval Comments")}: ____________________________________________', styles['VN']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f'{_("Approver")}: ____________________________________________  {_("Position")}: _______________', styles['VN']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f'{_("Approval Date")}: _______________', styles['VN']))
        elements.append(Spacer(1, 10))

        from reportlab.platypus import KeepTogether
        from reportlab.graphics.shapes import Drawing, Rect
        from reportlab.graphics import renderPDF
        from reportlab.platypus.flowables import Flowable
        
        class CheckBox(Flowable):
            def __init__(self, size=12):
                self.size = size
                self.width = size
                self.height = size
                
            def wrap(self, availWidth, availHeight):
                return (self.width, self.height)
                
            def draw(self):
                # Vẽ hình vuông trống
                self.canv.rect(0, 0, self.size, self.size, stroke=1, fill=0)
        # Status checkboxes
        approval_data = [
            [f'{_("Status")}:', CheckBox(), _('Approve'), CheckBox(), _('Reject')]
        ]
        approval_table = Table(approval_data, colWidths=[100, 15, 50, 15, 80])
        approval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'TimesNewRoman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (3, 0), (3, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(approval_table)

        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        filename = f"sample_approval_form_{self.code}_{fields.Date.today()}.pdf"
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

    def _generate_sample_code(self):
        # Get the next sequence number
        return self.env['ir.sequence'].next_by_code('garment.sample') or '/'