# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Billing",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Charge capture and invoicing on Odoo Accounting",
    "description": """
MEDIFLOW Billing
================
Healthcare charge capture and invoicing:

* mediflow.charge.master - chargeable service / price catalog (ChargeItemDefinition)
* mediflow.charge.item   - a captured charge from an encounter, lab order or
                           dispense (ChargeItem), drafted -> billed -> cancelled
* account.move (ext)     - links the invoice back to patient and encounter; the
                           ``invoice.posted`` and ``payment.received`` events are
                           emitted for the insurance/claims pipeline

Charges are captured from clinical events and aggregated into a single patient
invoice. The encounter exposes a 'Create Invoice' action.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_emr", "account"],
    "data": [
        "security/mediflow_billing_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_billing_data.xml",
        "views/mediflow_charge_master_views.xml",
        "views/mediflow_charge_item_views.xml",
        "views/account_move_views.xml",
        "views/mediflow_encounter_views.xml",
        "views/mediflow_billing_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
