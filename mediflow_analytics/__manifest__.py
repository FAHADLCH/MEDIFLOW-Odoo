# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Analytics",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Operational, clinical and revenue dashboards over SQL views",
    "description": """
MEDIFLOW Analytics
==================
Reporting layer for MEDIFLOW. Every KPI is sourced from a database ``VIEW`` exposed
as an ``auto=False`` Odoo model so aggregation happens in PostgreSQL, never row-by-row
in Python (see docs/phase-1/03-data-model.md scale rules). Each view carries
``company_id`` and is isolated by an ``ir.rule`` so multi-tenant reporting is safe.

Views
-----
* ``mediflow.v.queue.metrics``     - wait/service time, throughput, no-show (Dashboard 1)
* ``mediflow.v.appointment.util``  - utilization, cancellation, lead time (Dashboard 2)
* ``mediflow.v.lab.tat``           - turnaround, abnormal/critical rates (Dashboard 3)
* ``mediflow.v.revenue``           - collections, AR, patient responsibility (Dashboard 6)
* ``mediflow.v.claims``            - claim denial / adjudication (Dashboard 6)
* ``mediflow.v.clinical.quality``  - completion, amendments, break-glass (Dashboard 7)
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": [
        "mediflow_emr",
        "mediflow_queue",
        "mediflow_appointment",
        "mediflow_lab",
        "mediflow_billing",
        "mediflow_insurance",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/mediflow_analytics_security.xml",
        "views/mediflow_v_queue_metrics_views.xml",
        "views/mediflow_v_appointment_util_views.xml",
        "views/mediflow_v_lab_tat_views.xml",
        "views/mediflow_v_revenue_views.xml",
        "views/mediflow_v_claims_views.xml",
        "views/mediflow_v_clinical_quality_views.xml",
        "views/mediflow_analytics_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
