from odoo import http
from odoo.http import request

class GarmentOrderController(http.Controller):
    @http.route('/garment/order/get_order_cost_summary', type='json', auth='user')
    def get_order_cost_summary(self, order_id):
        order = request.env['garment.order'].browse(int(order_id))
        if order.exists():
            # Calculate material cost
            material_cost = 0
            if order.material_detail and len(order.material_detail) > 1:
                for row in order.material_detail[1:]:  # Skip header row
                    if len(row) >= 12:  # Ensure row has enough columns
                        total_quantity_used = float(row[10] or 0)  # Total Quantity Used
                        unit_price = float(row[11] or 0)  # Unit Price
                        material_cost += total_quantity_used * unit_price

            return {
                'material_cost': material_cost,
                'process_cost': sum(item.get('unit_price', 0) * item.get('multiplier', 1) for item in order.process_table[1:] if isinstance(item, dict)),
                'other_cost': sum(item.get('amount', 0) for item in order.other_cost if isinstance(item, dict))
            }
        return False

    @http.route('/garment/order/get_materials', type='json', auth='user')
    def get_materials(self, **kwargs):
        materials = request.env['garment.inventory.material'].search_read([], ['name', 'code'])
        return materials

    @http.route('/garment/order/get_colors', type='json', auth='user')
    def get_colors(self, **kwargs):
        colors = request.env['garment.inventory.color'].search_read([], ['name', 'code'])
        return colors 