# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Localization & Regions",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Global region profiles: language, currency, timezone & regulatory frameworks",
    "description": """
MEDIFLOW Localization & Regions
===============================
Make MEDIFLOW deployable anywhere in one click:

* Packaged region profiles (US, EU, UK, KSA, UAE, India, Singapore, Australia,
  Canada, Brazil) bundling language, currency, timezone and emergency number
* Regulatory frameworks (HIPAA, GDPR, PDPA, LGPD, PIPEDA) driving PHI retention,
  consent requirements and breach-notification windows
* Region-aware patient identifier labels (SSN, National ID, Aadhaar, Iqama, …)
* One-click apply to a company; multi-currency and multi-language ready
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "support": "info@sasystems.solutions",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "license": "LGPL-3",
    "depends": ["mediflow_base"],
    "data": [
        "security/ir.model.access.csv",
        "data/mediflow_region_profiles.xml",
        "views/mediflow_region_profile_views.xml",
        "views/mediflow_localization_menus.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
