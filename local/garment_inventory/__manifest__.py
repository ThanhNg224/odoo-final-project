{
    "name": "Garment Inventory Management",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base", "garment_base", "garment_authorization"],
    "data": [
        "views/inventory_receipt_view.xml",
        "views/color_inventory_view.xml",
        "views/material_inventory_view.xml",
        "views/order_inventory_view.xml",
        # "views/production_inventory_view.xml",
        "views/sample_inventory_view.xml",
        "views/base_menu.xml",
    ],
    
    "installable": True,
    "application": True,
    "auto_install": False,
    "assets": {
        "web.assets_backend": [
            "garment_inventory/static/src/components/receipt_line_treeview/treeview.js",
            "garment_inventory/static/src/components/receipt_line_treeview/treeview.xml",
        ],
    },
 
} # type: ignore
