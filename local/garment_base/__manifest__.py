# __manifest__.py
{
    "name": "Garment Base Module",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base"],
    "external_dependencies": {
        'python': ['xlsxwriter', 'reportlab'],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/qr_templates.xml",
        "data/garment_sequences.xml",
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

            # Material Issuance Table Components
            "/garment_base/static/src/components/material_issuance_table/header.xml",
            "/garment_base/static/src/components/material_issuance_table/header.js",
            "/garment_base/static/src/components/material_issuance_table/dialog.xml",
            "/garment_base/static/src/components/material_issuance_table/dialog.js",
            "/garment_base/static/src/components/material_issuance_table/style.scss",
        ],
    },
    "demo": [
        "data/demo_garment_sample.xml",
        "data/demo_garment_order.xml",
        "data/demo_orders.xml",
        "data/demo_progress.xml",
    ],
    "installable": True,
    "application": True,
}
