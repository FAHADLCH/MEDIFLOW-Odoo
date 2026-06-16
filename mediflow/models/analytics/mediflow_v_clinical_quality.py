# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MediflowVClinicalQuality(models.Model):
    """Read-only SQL view: one row per encounter with completion / completeness /
    amendment flags for the Clinical Quality dashboard (docs 08 §7).
    Documentation completeness proxies on chief complaint + assessment + plan."""

    _name = "mediflow.v.clinical.quality"
    _description = "Clinical Quality (view)"
    _auto = False
    _order = "start desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      readonly=True)
    encounter_type = fields.Selection([
        ("ambulatory", "Ambulatory"),
        ("emergency", "Emergency"),
        ("followup", "Follow-up"),
        ("virtual", "Virtual"),
    ], readonly=True)
    state = fields.Selection([
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ], readonly=True)
    start = fields.Datetime(readonly=True)
    is_completed = fields.Integer(string="Completed", readonly=True, aggregator="sum")
    is_amended = fields.Integer(string="Amended", readonly=True, aggregator="sum")
    is_documented = fields.Integer(string="Documented", readonly=True, aggregator="sum")
    encounter_count = fields.Integer(string="Encounters", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    e.id                AS id,
                    e.company_id        AS company_id,
                    e.practitioner_id   AS practitioner_id,
                    e.encounter_type    AS encounter_type,
                    e.state             AS state,
                    e.start             AS start,
                    CASE WHEN e.state IN ('completed', 'amended') THEN 1 ELSE 0 END
                                        AS is_completed,
                    CASE WHEN e.state = 'amended' THEN 1 ELSE 0 END AS is_amended,
                    CASE WHEN COALESCE(e.reason, '') != ''
                              AND e.assessment IS NOT NULL
                              AND e.plan IS NOT NULL
                         THEN 1 ELSE 0 END AS is_documented,
                    1                   AS encounter_count
                FROM mediflow_encounter e
            )
        """ % self._table)
