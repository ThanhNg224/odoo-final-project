from odoo import http
from odoo.http import request, route

class GarmentQRController(http.Controller):
    @http.route('/garment/scan_qr/<string:model>/<int:record_id>', type='http', auth='public', website=True)
    def scan_qr_info(self, model, record_id, **kwargs):
        """
        Route for displaying information from a scanned QR code
        The QR code should encode a URL with model name and record ID
        Example: /garment/scan_qr/garment.sample/1
                 /garment/scan_qr/garment.order/42
        """
        try:
            # Verify the model exists and is allowed to be accessed
            allowed_models = ['garment.sample', 'garment.order']
            if model not in allowed_models:
                return request.render('garment_base.qr_error_template', {
                    'error_message': f"Invalid model type: {model}"
                })
                
            # Try to find the record
            record = request.env[model].sudo().browse(record_id)
            
            if not record.exists():
                return request.render('garment_base.qr_error_template', {
                    'error_message': f"Record not found: {model} #{record_id}"
                })
                
            # Prepare data for the template based on model type
            if model == 'garment.sample':
                data = {
                    'title': f"Garment Sample: {record.name}",
                    'record': record,
                    'fields': [
                        {'label': 'Sample Number', 'value': record.number},
                        {'label': 'Shape', 'value': record.shape},
                        {'label': 'Color', 'value': record.color},
                        {'label': 'Client', 'value': record.client},
                        {'label': 'Brand', 'value': record.brand},
                        {'label': 'Status', 'value': dict(record._fields['state'].selection).get(record.state)},
                        {'label': 'Development Date', 'value': record.development_date},
                        {'label': 'Department', 'value': record.department_id.name if record.department_id else ''},
                    ],
                    'model': model,
                    'record_id': record_id,
                }
            elif model == 'garment.order':
                data = {
                    'title': f"Garment Order: {record.name}",
                    'record': record,
                    'fields': [
                        {'label': 'Order Number', 'value': record.order_number},
                        {'label': 'Shape', 'value': record.shape},
                        {'label': 'Color', 'value': record.color},
                        {'label': 'Quantity', 'value': record.quantity},
                        {'label': 'Unit Price', 'value': record.unit_price},
                        {'label': 'Issuing Company', 'value': record.issuing_company},
                        {'label': 'Receiving Company', 'value': record.receiving_company},
                        {'label': 'Cutting Date', 'value': record.cutting_date},
                    ],
                    'model': model,
                    'record_id': record_id,
                }
            
            return request.render('garment_base.qr_info_template', data)
            
        except Exception as e:
            return request.render('garment_base.qr_error_template', {
                'error_message': f"Error retrieving information: {str(e)}"
            })
    
    @http.route('/garment/qr/generate/<string:model>/<int:record_id>', type='http', auth='user', website=True)
    def generate_qr_code(self, model, record_id, **kwargs):
        """
        Route for generating a QR code for a garment record
        """
        try:
            # Verify the model exists and is allowed to be accessed
            allowed_models = ['garment.sample', 'garment.order']
            if model not in allowed_models:
                return request.render('garment_base.qr_error_template', {
                    'error_message': f"Invalid model type: {model}"
                })
                
            # Try to find the record
            record = request.env[model].sudo().browse(record_id)
            
            if not record.exists():
                return request.render('garment_base.qr_error_template', {
                    'error_message': f"Record not found: {model} #{record_id}"
                })
            
            # Generate the QR code for the record
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            qr_url = f"{base_url}/garment/scan_qr/{model}/{record_id}"
            
            return request.render('garment_base.qr_generate_template', {
                'title': f"QR Code for {record.name}",
                'record': record,
                'qr_url': qr_url,
                'model': model,
                'record_id': record_id,
            })
            
        except Exception as e:
            return request.render('garment_base.qr_error_template', {
                'error_message': f"Error generating QR code: {str(e)}"
            })
