from datetime import datetime
from odoo import http
from odoo.http import request, route
from odoo.tools.translate import _

class GarmentSampleController(http.Controller):    
    @http.route('/garment/sample/general_info', type='json', auth='user')
    def get_general_info(self):
        # Get current month and year for filtering
        current_year = datetime.now().year
        current_month = datetime.now().strftime("%m")
        date_filter = f"{current_month}/{current_year}"

        # Fetch data for each category
        current_month = datetime.now().month
        new_development_count = request.env['garment.sample'].sudo().search_count([
            ('state', '=', 'new'),
            ('development_date', '>=', f'{current_year}-{current_month:02d}-01'),
            ('development_date', '<=', f'{current_year}-{current_month:02d}-31')
        ])

        eliminated_count = request.env['garment.sample'].sudo().search_count([
            ('state', '=', 'eliminated'),
            ('update_date', '>=', f'{current_year}-{current_month:02d}-01'),
            ('update_date', '<=', f'{current_year}-{current_month:02d}-31')
        ])

        production_available_count = request.env['garment.sample'].sudo().search_count([
            ('state', '=', 'in_progress'),
            ('update_date', '>=', f'{current_year}-{current_month:02d}-01'),
            ('update_date', '<=', f'{current_year}-{current_month:02d}-31')
        ])

        return {
            "new_development": {
                "label": _("New development in %(date_filter)s, pending approval") % {'date_filter': date_filter},
                "count": new_development_count
            },
            "eliminated": {
                "label": _("Eliminated in %(date_filter)s") % {'date_filter': date_filter},
                "count": eliminated_count
            },
            "production_available": {
                "label": _("Production available in %(date_filter)s") % {'date_filter': date_filter},
                "count": production_available_count
            }
        }
    
    @http.route('/garment/sample/get_sample_cost_summary', type='json', auth='user')
    def get_sample_cost_summary(self, sample_id):
        sample = request.env['garment.sample'].browse(int(sample_id))
        if sample.exists():
            # Calculate material cost
            material_cost = 0
            if sample.material_detail and len(sample.material_detail) > 1:
                for row in sample.material_detail[1:]:  # Skip header row
                    if len(row) >= 12:  # Ensure row has enough columns
                        total_quantity_used = float(row[10] or 0)  # Total Quantity Used
                        unit_price = float(row[11] or 0)  # Unit Price
                        material_cost += total_quantity_used * unit_price
            return {
                'material_cost': material_cost,
                'process_cost': sum(item.get('unit_price', 0) * item.get('multiplier', 1) for item in sample.process_table[1:] if isinstance(item, dict)),
                'other_cost': sum(item.get('amount', 0) for item in sample.other_cost if isinstance(item, dict)),
                'quotation': sample.quotation or 0
            }
        return False 