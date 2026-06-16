# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Events",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Event-driven integration layer: domain events, webhooks, live bus",
    "description": """
MEDIFLOW Events
===============
Self-contained event-driven integration layer:

* EventMixin        - ``_emit_event(name, payload)`` for any model
* mediflow.event    - durable event store with retry/replay state
* mediflow.webhook  - outbound HMAC-signed webhook subscriptions
* Cron-based delivery worker (works without external job runners; can be swapped
  for OCA ``queue_job`` in production)
* Live UI notifications via ``bus.bus``
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_base", "bus"],
    "data": [
        "security/ir.model.access.csv",
        "data/mediflow_events_cron.xml",
        "views/mediflow_event_views.xml",
        "views/mediflow_webhook_views.xml",
        "views/mediflow_events_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
