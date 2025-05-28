# __manifest__.py
{
    "name": "Garment Base Modules",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base"],
    "external_dependencies": {
        'python': ['xlsxwriter', 'reportlab'],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/qr_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Finished Product Size Table Components
            "/garment_base/static/src/components/finished_product_size_table/table.scss",
            "/garment_base/static/src/components/finished_product_size_table/table.js",
            "/garment_base/static/src/components/finished_product_size_table/table.xml",
            
            # Process Table Components
            "/garment_base/static/src/components/process_table/table.scss",
            "/garment_base/static/src/components/process_table/table.js",
            "/garment_base/static/src/components/process_table/table.xml",
            
            # Other Cost Table Components
            "/garment_base/static/src/components/other_cost_table/table.scss",
            "/garment_base/static/src/components/other_cost_table/table.js",
            "/garment_base/static/src/components/other_cost_table/table.xml",
            
            # Material Detail Table Components
            "/garment_base/static/src/components/material_detail_table/table.scss",
            "/garment_base/static/src/components/material_detail_table/table.js",
            "/garment_base/static/src/components/material_detail_table/table.xml",
            
            # Progress Table Components
            "/garment_base/static/src/components/progress_table/table.scss",
            "/garment_base/static/src/components/progress_table/table.js",
            "/garment_base/static/src/components/progress_table/table.xml",

            # Specification Detail Table Components
            "/garment_base/static/src/components/specification_detail_table/table.scss",
            "/garment_base/static/src/components/specification_detail_table/table.js",
            "/garment_base/static/src/components/specification_detail_table/table.xml",\
            
            
        ],
    },
    "demo": [
        "data/demo_garment_sample.xml",
        "data/demo_garment_order.xml",

        # From production_management
        "data/production_sequence.xml",
        "data/demo_orders.xml",
        "data/demo_progress.xml",
    ],
    "installable": True,
    "application": True,
}
