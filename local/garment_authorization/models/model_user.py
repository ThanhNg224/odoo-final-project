from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    garment_group_id = fields.Many2one('garment.group', string='Group')

    @api.model
    def create(self, vals):
        user = super().create(vals)
        if vals.get('garment_group_id'):
            garment_group = self.env['garment.group'].browse(vals['garment_group_id'])
            # All possible garment permission groups (from all garment groups)
            all_permission_groups = self.env['garment.permission'].search([]).mapped('group_id')
            # Remove all garment permission groups from user, keep all other groups
            user_groups = user.groups_id - all_permission_groups
            # Add the new permission groups from this garment group
            permission_groups = garment_group.permission_ids.mapped('group_id')
            # Combine
            new_groups = user_groups | permission_groups
            user.groups_id = [(6, 0, new_groups.ids)]
        return user

    def write(self, vals):
        res = super().write(vals)
        if 'garment_group_id' in vals:
            for user in self:
                if user.garment_group_id:
                    garment_group = user.garment_group_id
                    # All possible garment permission groups (from all garment groups)
                    all_permission_groups = self.env['garment.permission'].search([]).mapped('group_id')
                    # Remove all garment permission groups from user, keep all other groups
                    user_groups = user.groups_id - all_permission_groups
                    # Add the new permission groups from this garment group
                    permission_groups = garment_group.permission_ids.mapped('group_id')
                    # Combine
                    new_groups = user_groups | permission_groups
                    user.groups_id = [(6, 0, new_groups.ids)]
        return res
