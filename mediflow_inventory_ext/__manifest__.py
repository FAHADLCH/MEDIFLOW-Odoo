# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Inventory Extension",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Pharmaceutical inventory: drug attributes, lot expiry, FEFO, reorder",
    "description": """
MEDIFLOW Inventory Extension
============================
Extends Odoo Inventory for healthcare:

* product.template / product.product - drug class, ATC code, controlled flag,
  prescription-required flag, dispensing form, strength
* stock.lot                          - expiry date with FEFO selection helper and
  expired-lot dispensing guard
* Near-expiry flagging cron

Provides the ``_select_fefo_lot`` and ``_get_available_qty`` helpers consumed by
the pharmacy module.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["stock", "mediflow_base"],
    "data": [
        "data/mediflow_inventory_data.xml",
        "views/product_views.xml",
        "views/stock_lot_views.xml",
        "views/mediflow_inventory_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
