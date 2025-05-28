{
    "name": "Garment Production",
    "version": "1.0",
    "summary": "Manage manufacturing production steps for garment company",
    "category": "Manufacturing",
    "author": "Siu",
    "depends": ["base", "garment_base"],
    "data": [
        "views/production_order_views.xml",
        "views/production_progress_views.xml",
        "views/operation_price_views.xml",
        "views/product_style_views.xml",
        "views/production_order_line_views.xml",
        "views/production_bundle_views.xml",
        "views/production_worker_entry_views.xml",
        "views/production_distribution_views.xml",
        "views/stock_production_inout_views.xml",
        "views/production_salary_adjust_views.xml",
        "views/production_process_views.xml",
        "views/production_cost_views.xml",
        "views/production_material_views.xml",
        "reports/bundle_report.xml",
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
