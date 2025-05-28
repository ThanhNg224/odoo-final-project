# __manifest__.py
{
    "name": "Garment Order Management",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base", "garment_base"],
    "external_dependencies": {
        'python': ['xlsxwriter', 'reportlab'],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/order_view.xml",
        "views/base_menu.xml",
    ],
    
    "assets": {
        "web.assets_backend": [
            "garment_order/static/src/components/header_button/create_button.js",
            "garment_order/static/src/components/header_button/create_button.xml",
        ],
    },
    "installable": True,
    "application": True,
} # type: ignore
