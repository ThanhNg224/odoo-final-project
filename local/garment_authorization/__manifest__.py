{
    "name": "Garment Authorization Management",
    "author": "Phung Minh Chien",
    "license": "LGPL-3",
    "depends": ["web", "base", "garment_base"],

    "data": [
        "data/permission_data.xml",
        "security/ir.model.access.csv",
        "views/group_view.xml",
        "views/user_view.xml",
        "views/permission_view.xml",
        "views/base_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
        ],
    },
    "installable": True,
    "application": True,
} # type: ignore
