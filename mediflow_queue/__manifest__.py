# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Queue",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Queue management: service points, tokens, call-next, live board",
    "description": """
MEDIFLOW Queue
==============
Per-clinic, per-service-point queue management:

* mediflow.queue        - service point queue definition (reception, triage, doctor, lab, pharmacy)
* mediflow.queue.entry  - token / ticket with full lifecycle

Live board updates are pushed through the MEDIFLOW event bus. Wait/serve metrics
feed the analytics module.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_emr", "bus"],
    "data": [
        "security/mediflow_queue_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_queue_data.xml",
        "views/mediflow_queue_views.xml",
        "views/mediflow_queue_entry_views.xml",
        "views/mediflow_queue_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
