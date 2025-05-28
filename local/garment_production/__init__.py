def post_init_hook(cr, registry):
    """Post init hook to clean up invalid Other cost entries."""
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    production_orders = env['production.order'].search([])
    for order in production_orders:
        order.action_remove_other_cost_entries()
