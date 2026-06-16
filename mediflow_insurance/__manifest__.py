# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Insurance",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Payers, coverage, pre-authorization and claims",
    "description": """
MEDIFLOW Insurance
==================
Payer and claims management:

* mediflow.payer    - insurance organization (FHIR Organization)
* mediflow.coverage - a patient's policy with a payer (FHIR Coverage)
* mediflow.preauth  - pre-authorization (requested -> approved / denied / expired)
* mediflow.claim    - claim lifecycle (draft -> submitted -> adjudicated ->
                      paid / denied -> appealed -> submitted) with claim lines and
                      patient-responsibility recomputation on adjudication
* mediflow.claim.line - per-charge claim detail

Adjudication updates the patient balance and emits ``claim.adjudicated`` /
``claim.denied``; submission emits ``claim.submitted``. A daily cron expires stale
pre-authorizations.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_billing"],
    "data": [
        "security/mediflow_insurance_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_insurance_data.xml",
        "views/mediflow_payer_views.xml",
        "views/mediflow_coverage_views.xml",
        "views/mediflow_preauth_views.xml",
        "views/mediflow_claim_views.xml",
        "views/mediflow_insurance_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
