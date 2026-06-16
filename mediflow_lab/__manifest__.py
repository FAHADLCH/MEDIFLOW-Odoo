# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Laboratory",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Diagnostics: test catalog, panels, orders, specimens, verified results",
    "description": """
MEDIFLOW Laboratory
===================
Diagnostic workflow for clinics and reference labs:

* mediflow.lab.test    - analyte catalog (LOINC), reference ranges, critical thresholds
* mediflow.lab.panel   - groupings of tests
* mediflow.lab.order   - ServiceRequest (ordered -> collected -> received ->
                         in_process -> resulted -> completed)
* mediflow.specimen    - collected sample with accession identifier
* mediflow.lab.result  - Observation (preliminary -> verified -> released -> amended)
                         with hard immutability on released rows and versioned
                         amendments

Critical-value detection raises ``lab.critical.flagged`` independent of workflow
state. Released results are exposed to the portal and projected as FHIR
DiagnosticReport / Observation by the FHIR module.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_emr"],
    "data": [
        "security/mediflow_lab_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_lab_data.xml",
        "views/mediflow_lab_test_views.xml",
        "views/mediflow_lab_panel_views.xml",
        "views/mediflow_lab_order_views.xml",
        "views/mediflow_specimen_views.xml",
        "views/mediflow_lab_result_views.xml",
        "views/mediflow_lab_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
