from odoo import http
from odoo.http import request

class GarmentInventoryController(http.Controller):
    @http.route('/garment/inventory/get_material_details', type='json', auth='user')
    def get_material_details(self, material_id):
        material = request.env['garment.inventory.material'].sudo().browse(int(material_id))
        if material.exists():
            return {
                'unit': material.unit,
                'unit_price': material.unit_price,
                'supplier': material.supplier,
            }
        return False 