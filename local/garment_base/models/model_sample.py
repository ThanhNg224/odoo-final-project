import base64
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
import json
import io
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class Sample(models.Model):
    _name = 'garment.sample'
    _description = 'Garment Sample'

    name = fields.Char(string='Name', required=True)
    number = fields.Char(string='Sample Number')
    shape = fields.Char(string='Shape')
    color = fields.Char(string='Color')
    brand = fields.Char(string='Brand')
    client = fields.Char(string='Client')
    quotation = fields.Integer(string='Quotation')
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
    process_table = fields.Json(string='Process Table', default=lambda self: [{"name": "", "unit_price": 0, "multiplier": 1, "notes": ""}])
    other_cost = fields.Json(string='Other Costs', default=lambda self: [{"cost_name": "", "amount": 0}])

    progress_detail = fields.Json(string='Progress Detail', default=lambda self: [])
    process_requirements = fields.Html(string='Process Requirements')
    remark = fields.Html(string='Remarks')
    state = fields.Selection([
        ('new', 'New development, pending approval'),
        ('in_progress', 'Can be produced'),
        ('eliminated', 'Eliminated')
    ])

    department_id = fields.Many2one('garment.department', string='Department')
    published_by = fields.Many2one('res.users', string='Published By', default=lambda self: self.env.user)
    image_detail = fields.Binary(string='Image Details', attachment=True)
    related_document = fields.Binary(string='Related Documents', attachment=True)

    all_samples = fields.Many2many('garment.sample', compute='_compute_all_samples', string="All Samples")

    @api.depends()
    def _compute_all_samples(self):
        for record in self:
            record.all_samples = self.env['garment.sample'].search([])

    @api.model
    def create(self, vals):
        for key in ['finished_product_size', 'material_detail', 'process_table', 'other_cost']:
            if key in vals and isinstance(vals[key], str):
                try:
                    vals[key] = json.loads(vals[key])
                except Exception:
                    pass
        
        return super().create(vals)

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

    def action_open_pmc_form(self):
        return {
            'name': 'Create PMC Sample',
            'type': 'ir.actions.act_window',
            'res_model': 'garment.sample',
            'view_mode': 'form',
            'view_id': self.env.ref('garment_sample.view_garment_sample_form_edit').id,
            'target': 'current',
            'context': {'default_state': 'new'},
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

    def action_export_pdf(self):
        self.ensure_one()
        
        # Create a PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title = Paragraph(f"Sample Report: {self.name}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Basic Info
        basic_info = [
            ['Field', 'Value'],
            ['Sample Name', self.name],
            ['Number', self.number],
            ['Shape', self.shape],
            ['Color', self.color],
            ['Client', self.client],
            ['Brand', self.brand],
            ['Designer', self.designer],
            ['Quantity', str(self.quantity)],
            ['Pattern Size', self.pattern_size],
            ['Development Date', str(self.development_date)],
        ]
        
        t = Table(basic_info, colWidths=[200, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Add Finished Product Size
        if self.finished_product_size:
            elements.append(Paragraph("Finished Product Size", styles['Heading2']))
            elements.append(Spacer(1, 10))
            t = Table(self.finished_product_size)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))
        
        # Add Material Detail
        if self.material_detail:
            elements.append(Paragraph("Material Detail", styles['Heading2']))
            elements.append(Spacer(1, 10))
            t = Table(self.material_detail)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f"sample_{self.name}_{fields.Date.today()}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        
        # Return download URL
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_export_xlsx(self):
        self.ensure_one()
        
        # Create a new Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Add a worksheet
        worksheet = workbook.add_worksheet('Sample Details')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Write Basic Info
        worksheet.write(0, 0, 'Sample Report', header_format)
        worksheet.merge_range(0, 0, 0, 1, f'Sample Report: {self.name}', header_format)
        
        basic_info = [
            ['Field', 'Value'],
            ['Sample Name', self.name],
            ['Number', self.number],
            ['Shape', self.shape],
            ['Color', self.color],
            ['Client', self.client],
            ['Brand', self.brand],
            ['Designer', self.designer],
            ['Quantity', str(self.quantity)],
            ['Pattern Size', self.pattern_size],
            ['Development Date', str(self.development_date)],
        ]
        
        for row_num, row_data in enumerate(basic_info, start=2):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_data, cell_format)
        
        # Write Finished Product Size
        if self.finished_product_size:
            row_num = len(basic_info) + 4
            worksheet.write(row_num, 0, 'Finished Product Size', header_format)
            worksheet.merge_range(row_num, 0, row_num, len(self.finished_product_size[0])-1, 'Finished Product Size', header_format)
            
            for row_idx, row_data in enumerate(self.finished_product_size, start=row_num+1):
                for col_idx, cell_data in enumerate(row_data):
                    worksheet.write(row_idx, col_idx, cell_data, cell_format)
        
        # Write Material Detail
        if self.material_detail:
            row_num = len(basic_info) + len(self.finished_product_size) + 6
            worksheet.write(row_num, 0, 'Material Detail', header_format)
            worksheet.merge_range(row_num, 0, row_num, len(self.material_detail[0])-1, 'Material Detail', header_format)
            
            for row_idx, row_data in enumerate(self.material_detail, start=row_num+1):
                for col_idx, cell_data in enumerate(row_data):
                    worksheet.write(row_idx, col_idx, cell_data, cell_format)
        
        # Close workbook
        workbook.close()
        xlsx_content = output.getvalue()
        output.close()
        
        # Create attachment
        filename = f"sample_{self.name}_{fields.Date.today()}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        
        # Return download URL
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }