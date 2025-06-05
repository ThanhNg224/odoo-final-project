from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class GarmentGroup(models.Model):
    _name = "garment.group"
    _description = "Garment Group"

    name = fields.Char(string="Group Name", required=True)
    permission_ids = fields.Many2many('garment.permission', string='Permissions')

    group_ids = fields.Many2many('res.groups', string='Groups', compute='_compute_groups', store=True)

    @api.depends('permission_ids')
    def _compute_groups(self):
        for rec in self:
            rec.group_ids = rec.permission_ids.mapped('group_id')

    def write(self, vals):
        res = super().write(vals)
        if 'permission_ids' in vals:
            self._update_users_groups()
        return res

    def _update_users_groups(self):
        """Update groups for all users that belong to this garment group, preserving all other default groups."""
        for group in self:
            users = self.env['res.users'].search([('garment_group_id', '=', group.id)])
            if not users:
                continue

            # All possible garment permission groups (from all garment groups)
            all_permission_groups = self.env['garment.permission'].search([]).mapped('group_id')

            for user in users:
                # Remove all garment permission groups from user, keep all other groups
                user_groups = user.groups_id - all_permission_groups
                # Add the new permission groups from this garment group
                permission_groups = group.permission_ids.mapped('group_id')
                # Combine
                new_groups = user_groups | permission_groups
                user.groups_id = [(6, 0, new_groups.ids)]


class GarmentPermission(models.Model):
    _name = 'garment.permission'
    _description = 'Permission for Garment Actions'

    name = fields.Char(required=True)
    group_id = fields.Many2one('res.groups', string='Related Group')