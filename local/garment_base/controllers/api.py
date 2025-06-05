from datetime import datetime
from odoo import http
from odoo.http import request, route
from odoo.tools.translate import _

class GarmentController(http.Controller):
    @http.route('/garment/get_template', type='json', auth='user')
    def get_template(self, template_id, model):
        template = request.env[model].sudo().browse(int(template_id))
        if template.exists():
            return {
                'table_data': template.template,
                'name': template.name
            }
        return False

    @http.route('/garment/get_templates', type='json', auth='user')
    def get_templates(self, model):
        templates = request.env[model].sudo().search_read([], ['id', 'name'])
        return templates

    @http.route('/garment/save_template', type='json', auth="user")
    def save_template(self, name, table_data, model):
        try:
            # Directly create the template in the target model
            template = request.env[model].sudo().create({
                'name': name,
                'template': table_data,
            })
            return {
                'success': True,
                'template_id': template.id,
                'name': template.name
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/garment/get_materials', type='json', auth='user')
    def get_materials(self):
        materials = request.env['garment.inventory.material'].sudo().search_read(
            [], ['name', 'code']
        )
        return materials

    @http.route('/garment/get_colors', type='json', auth='user')
    def get_colors(self):
        colors = request.env['garment.inventory.color'].sudo().search_read(
            [], ['name', 'code']
        )
        return colors 

    @http.route('/garment/department/search_read', type='json', auth='user')
    def search_departments(self, fields=None, domain=None):
        if fields is None:
            fields = ['id', 'name']
        if domain is None:
            domain = []
        departments = request.env['garment.department'].sudo().search_read(domain, fields)
        return departments

    @http.route('/garment/check_permission', type='json', auth='user')
    def check_permission(self, permission_name):
        user = request.env.user
        has_permission = user.has_group(permission_name)
        return {
            'has_permission': has_permission,
            'user_id': user.id,
            'user_name': user.name
        }
    