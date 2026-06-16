# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Theme & UX",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "SA Systems brand theme, login branding, and UI/UX polish for MEDIFLOW",
    "description": """
MEDIFLOW Theme & UX
===================
Applies the SA Systems brand system across the MEDIFLOW platform:

* Brand color tokens, gradient navbar, refined cards and form chrome
* MEDIFLOW / SA Systems login and footer branding
* High-resolution vector logos (swap-in ready)
* Accessibility-minded contrast and focus states
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "support": "info@sasystems.solutions",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "license": "LGPL-3",
    "depends": ["web", "mediflow_base"],
    "data": [
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mediflow_theme/static/src/scss/mediflow_backend.scss",
        ],
        "web.assets_frontend": [
            "mediflow_theme/static/src/scss/mediflow_frontend.scss",
        ],
    },
    "images": ["static/description/banner.svg"],
    "application": False,
    "installable": True,
    "auto_install": False,
}
