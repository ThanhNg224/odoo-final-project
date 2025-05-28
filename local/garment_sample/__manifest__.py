# __manifest__.py
{
    "name": "Garment Sample Management",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base", "garment_base"],
    "external_dependencies": {
        'python': ['xlsxwriter', 'reportlab'],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/sample_view.xml",
        "views/table_template_view.xml",
        "views/base_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Core dependencies
            "/garment_sample/static/src/js/dropdown_handler.js",
            
            # XML Templates first
            "/garment_sample/static/src/components/header_button/create_button.xml",
            "/garment_sample/static/src/components/general_info/general_info.xml",
            "/garment_sample/static/src/components/sample_cost_summary_table/sample_cost_summary_table.xml",
            
            # SCSS files
            "/garment_sample/static/src/components/general_info/general_info.scss",
            "/garment_sample/static/src/components/sample_cost_summary_table/sample_cost_summary_table.scss",
            
            # JavaScript files last
            "/garment_sample/static/src/components/header_button/create_button.js",
            "/garment_sample/static/src/components/general_info/general_info.js",
            "/garment_sample/static/src/components/sample_cost_summary_table/sample_cost_summary_table.js",
        ],
    },
    "installable": True,
    "application": True,
} # type: ignore
