# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Patient Portal",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Patient self-service portal: appointments, results, invoices, consent",
    "description": """
MEDIFLOW Patient Portal
=======================
Self-service surface for patients on the Odoo website/portal:

* Portal home counters for appointments, released results and invoices
* /my/appointments       - list and detail of the patient's own appointments
* /my/lab-results        - released, consent-gated lab results only
* /my/invoices           - patient invoices with online payment hand-off
* /my/consents           - view and (where allowed) revoke data-sharing consents

All controllers resolve the signed-in user to their ``mediflow.patient`` and refuse
access to any record that is not owned by that patient. Lab results are shown only
when released AND the patient has an active data-sharing consent.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": [
        "mediflow_emr",
        "mediflow_appointment",
        "mediflow_lab",
        "mediflow_billing",
        "portal",
        "website",
    ],
    "data": [
        "security/mediflow_portal_security.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
