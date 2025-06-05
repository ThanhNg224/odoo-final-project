{
    "name": "Garment Production",
    "version": "1.0",
    "summary": "Manage manufacturing production steps for garment company",
    "category": "Manufacturing",
    "author": "Siu",
    "depends": ["web", "base", "garment_base", "garment_authorization"],
    "data": [
        # Views
        "views/base_menu.xml",
        "views/approval_request_views.xml",
        "views/operation_price_views.xml",
        "views/production_approval_views.xml",
        "views/production_bundle_views.xml",
        "views/production_cost_views.xml",
        "views/production_distribution_views.xml",
        "views/production_finance_approval_views.xml",
        "views/production_material_views.xml",
        "views/production_order_line_views.xml",
        "views/production_order_views.xml",
        "views/production_process_views.xml",
        "views/production_progress_views.xml",
        "views/production_salary_adjust_views.xml",
        "views/production_size_chart_views.xml",
        "views/production_worker_entry_views.xml",
        "views/product_lot_views.xml",
        "views/product_style_views.xml",
        "views/stock_production_inout_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "assets": {
        "web.assets_backend": [
            "garment_production/static/src/scss/production_management.scss",
        ],
    }
}
