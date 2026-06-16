# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowVitalSign(models.Model):
    """Vital signs reading. Projects to FHIR ``Observation`` (vital-signs).

    Kept deliberately narrow (one row per reading set) so the table stays
    partition-friendly as it grows to tens of millions of rows."""

    _name = "mediflow.vital.sign"
    _description = "Vital Signs"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "measured_at desc, id desc"

    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter",
                                   index=True, ondelete="set null")
    measured_at = fields.Datetime(string="Measured At", default=fields.Datetime.now,
                                  required=True, index=True)
    measured_by_id = fields.Many2one("mediflow.practitioner", string="Measured By")

    temperature = fields.Float(string="Temp (°C)")
    pulse = fields.Integer(string="Pulse (bpm)")
    respiratory_rate = fields.Integer(string="Resp. Rate")
    systolic = fields.Integer(string="Systolic (mmHg)")
    diastolic = fields.Integer(string="Diastolic (mmHg)")
    spo2 = fields.Float(string="SpO2 (%)")
    weight = fields.Float(string="Weight (kg)")
    height = fields.Float(string="Height (cm)")
    bmi = fields.Float(string="BMI", compute="_compute_bmi", store=True)
    pain_score = fields.Integer(string="Pain (0-10)")
    note = fields.Text()

    @api.depends("weight", "height")
    def _compute_bmi(self):
        for vital in self:
            if vital.weight and vital.height:
                meters = vital.height / 100.0
                vital.bmi = round(vital.weight / (meters * meters), 1)
            else:
                vital.bmi = 0.0
