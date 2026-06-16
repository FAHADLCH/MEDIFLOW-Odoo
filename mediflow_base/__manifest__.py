# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Base",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "MEDIFLOW kernel: shared mixins, security groups, PHI audit, configuration",
    "description": """
MEDIFLOW Base
=============
Foundation module for the MEDIFLOW healthcare platform. Provides:

* StateMachineMixin  - declarative, audited, guard-protected state transitions
* PhiAuditMixin      - append-only PHI access/change audit
* CompanyScopeMixin  - mandatory multi-clinic (res.company) scoping
* mediflow.audit.log - append-only audit storage
* Security group hierarchy shared across all MEDIFLOW modules
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/mediflow_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_data.xml",
        "views/mediflow_audit_log_views.xml",
        "views/mediflow_menus.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
