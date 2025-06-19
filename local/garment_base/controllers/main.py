from odoo import http
from odoo.http import request
import json

class GarmentController(http.Controller):
    @http.route('/garment/get_materials', type='json', auth='user')
    def get_materials(self, **kwargs):
        materials = request.env['garment.inventory.material'].sudo().search_read([], ['code', 'name', 'unit', 'unit_price'])
        return materials
