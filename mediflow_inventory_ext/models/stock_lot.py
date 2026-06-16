# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    mediflow_expiry_date = fields.Date(string="Expiry Date", index=True,
                                       help="Expiry used by MEDIFLOW FEFO selection "
                                       "and expired-lot dispensing guard.")
    is_expired = fields.Boolean(string="Expired", compute="_compute_is_expired",
                                search="_search_is_expired")
    near_expiry = fields.Boolean(string="Near Expiry", default=False)

    @api.depends("mediflow_expiry_date")
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for lot in self:
            lot.is_expired = bool(lot.mediflow_expiry_date and
                                  lot.mediflow_expiry_date < today)

    def _search_is_expired(self, operator, value):
        today = fields.Date.context_today(self)
        expired_domain = [("mediflow_expiry_date", "<", today)]
        if (operator == "=" and value) or (operator == "!=" and not value):
            return expired_domain
        return ["|", ("mediflow_expiry_date", "=", False),
                ("mediflow_expiry_date", ">=", today)]

    @api.model
    def _select_fefo_lot(self, product, qty_needed, location=None):
        """First-Expire-First-Out lot selection for a product. Returns a list of
        ``(lot, qty)`` tuples drawing from non-expired lots in expiry order, never
        exceeding available stock. Expired lots are excluded entirely."""
        today = fields.Date.context_today(self)
        Quant = self.env["stock.quant"]
        domain = [
            ("product_id", "=", product.id),
            ("location_id.usage", "=", "internal"),
            ("quantity", ">", 0),
        ]
        if location:
            domain.append(("location_id", "child_of", location.id))
        quants = Quant.search(domain)
        # Group available qty per lot, excluding expired lots.
        per_lot = {}
        for quant in quants:
            lot = quant.lot_id
            if not lot:
                continue
            if lot.mediflow_expiry_date and lot.mediflow_expiry_date < today:
                continue
            per_lot.setdefault(lot, 0.0)
            per_lot[lot] += quant.quantity
        # Sort by expiry (earliest first); undated lots last.
        ordered = sorted(
            per_lot.items(),
            key=lambda kv: (kv[0].mediflow_expiry_date or fields.Date.to_date("2999-12-31")))
        allocation = []
        remaining = qty_needed
        for lot, available in ordered:
            if remaining <= 0:
                break
            take = min(available, remaining)
            allocation.append((lot, take))
            remaining -= take
        return allocation, remaining

    @api.model
    def cron_flag_near_expiry(self, days=90):
        """Flag lots expiring within ``days`` that still have stock."""
        from datetime import timedelta
        today = fields.Date.context_today(self)
        horizon = today + timedelta(days=days)
        lots = self.search([
            ("mediflow_expiry_date", "!=", False),
            ("mediflow_expiry_date", "<=", horizon),
            ("mediflow_expiry_date", ">=", today),
        ])
        for lot in lots:
            if not lot.near_expiry:
                lot.near_expiry = True
                if hasattr(lot, "_emit_event"):
                    lot._emit_event("inventory.expiry.flagged",
                                    {"lot_id": lot.id, "product_id": lot.product_id.id})
        return True
