# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Integrations",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Payments, SMS/WhatsApp, telehealth, HL7/lab inbound and clearinghouse connectors",
    "description": """
MEDIFLOW Integrations
=====================
A pluggable connector framework with batteries included:

* Payments — Stripe payment links for patient-responsibility invoices
* Messaging — Twilio SMS / WhatsApp appointment reminders and result notices
* Telehealth — one-click secure video rooms for virtual encounters
* Lab / HL7 — authenticated inbound endpoint that ingests HL7 v2 / FHIR messages
  into a processing inbox and emits durable events
* Extensible registry for e-prescribing, insurance clearinghouses, accounting
  and calendar systems

Every connector is consent-aware, fully audited, and degrades gracefully when a
provider is unreachable — it never blocks clinical workflows.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "support": "info@sasystems.solutions",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "license": "LGPL-3",
    "depends": [
        "mediflow_base",
        "mediflow_events",
        "mediflow_emr",
        "mediflow_appointment",
        "mediflow_billing",
    ],
    "data": [
        "security/mediflow_integrations_security.xml",
        "security/ir.model.access.csv",
        "views/mediflow_integration_views.xml",
        "views/mediflow_integration_log_views.xml",
        "views/mediflow_integration_message_views.xml",
        "views/mediflow_appointment_views.xml",
        "views/mediflow_integration_menus.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
