# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_medication = fields.Boolean(string="Is Medication", default=False)
    drug_class = fields.Char(string="Drug Class")
    atc_code = fields.Char(string="ATC Code", help="Anatomical Therapeutic Chemical code "
                           "for FHIR Medication coding.")
    rxnorm_code = fields.Char(string="RxNorm Code")
    is_controlled = fields.Boolean(string="Controlled Substance", default=False)
    prescription_required = fields.Boolean(string="Prescription Required", default=True)
    dosage_form = fields.Selection([
        ("tablet", "Tablet"),
        ("capsule", "Capsule"),
        ("syrup", "Syrup"),
        ("injection", "Injection"),
        ("cream", "Cream / Ointment"),
        ("drops", "Drops"),
        ("inhaler", "Inhaler"),
        ("other", "Other"),
    ], string="Dosage Form")
    strength = fields.Char(string="Strength", help="e.g. '500 mg', '5 mg/ml'.")

    @api.onchange("is_medication")
    def _onchange_is_medication(self):
        if self.is_medication:
            # Medications must be lot/expiry tracked.
            self.tracking = "lot"
            self.use_expiration_date = True


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_available_qty(self, location=None):
        """Return on-hand quantity for this product (optionally at a location)."""
        self.ensure_one()
        quants = self.env["stock.quant"].search([
            ("product_id", "=", self.id),
            ("location_id.usage", "=", "internal"),
        ] + ([("location_id", "child_of", location.id)] if location else []))
        return sum(quants.mapped("quantity"))
