# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Pharmacy",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Prescriptions, allergy/interaction checks, FEFO dispensing",
    "description": """
MEDIFLOW Pharmacy
=================
Medication ordering and dispensing:

* mediflow.prescription       - MedicationRequest (draft -> ordered ->
                                partially_dispensed / dispensed -> handed_over)
* mediflow.prescription.line  - one ordered medication with dose/frequency/duration
* mediflow.dispense           - dispensing event (draft -> confirmed -> done) that
                                allocates stock by FEFO and blocks expired lots
* mediflow.dispense.line      - per-medication fill with lot allocation

Allergy and drug-class interaction checks run on the draft -> ordered transition and
require an audited override to bypass. Dispensing consumes the inventory FEFO helper
and posts stock moves; ``pharmacy.dispensed`` is emitted for billing capture.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_emr", "mediflow_inventory_ext"],
    "data": [
        "security/mediflow_pharmacy_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_pharmacy_data.xml",
        "views/mediflow_dispense_views.xml",
        "views/mediflow_prescription_views.xml",
        "views/mediflow_pharmacy_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
