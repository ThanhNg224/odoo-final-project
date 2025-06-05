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
        "views/qr_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Finished Product Size Table Components
            "/garment_base/static/src/components/finished_product_size_table/table.xml",
            "/garment_base/static/src/components/finished_product_size_table/table.scss",
            "/garment_base/static/src/components/finished_product_size_table/table.js",
            
            # Process Table Components
            "/garment_base/static/src/components/process_table/table.scss",
            "/garment_base/static/src/components/process_table/table.js",
            "/garment_base/static/src/components/process_table/table.xml",
            
            # Other Cost Table Components
            "/garment_base/static/src/components/other_cost_table/table.xml",
            "/garment_base/static/src/components/other_cost_table/table.scss",
            "/garment_base/static/src/components/other_cost_table/table.js",
            
            # Material Detail Table Components
            "/garment_base/static/src/components/material_detail_table/table.xml",
            "/garment_base/static/src/components/material_detail_table/table.scss",
            "/garment_base/static/src/components/material_detail_table/table.js",
            
            # Progress Table Components
            "/garment_base/static/src/components/progress_table/table.xml",
            "/garment_base/static/src/components/progress_table/table.scss",
            "/garment_base/static/src/components/progress_table/table.js",

            # Specification Detail Table Components
            "/garment_base/static/src/components/specification_detail_table/table.xml",
            "/garment_base/static/src/components/specification_detail_table/table.scss",
            "/garment_base/static/src/components/specification_detail_table/table.js",

            # Progress Table From Model Components
            "/garment_base/static/src/components/progress_dropdown_from_model/table.xml",
            "/garment_base/static/src/components/progress_dropdown_from_model/table.scss",
            "/garment_base/static/src/components/progress_dropdown_from_model/table.js",

            # Many2Many Image Components
            "/garment_base/static/src/components/custom_m2m_image/m2m_image.xml",
            "/garment_base/static/src/components/custom_m2m_image/m2m_image.scss",
            "/garment_base/static/src/components/custom_m2m_image/m2m_image.js",
        ],
    },
    "demo": [
        "data/demo_garment_sample.xml",
        "data/demo_garment_order.xml",
        "data/demo_orders.xml",
        "data/demo_progress.xml",
        "data/production_sequence.xml",
    ],
    "installable": True,
    "application": True,
}
