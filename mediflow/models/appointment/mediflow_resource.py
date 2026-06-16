# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowResource(models.Model):
    """A bookable physical resource: consultation room, procedure room, or a
    piece of equipment. Projects to FHIR ``Location`` or ``Device``."""

    _name = "mediflow.resource"
    _description = "Clinical Resource"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "name"

    name = fields.Char(required=True, index=True)
    resource_type = fields.Selection([
        ("room", "Room"),
        ("equipment", "Equipment"),
        ("bay", "Bay / Chair"),
    ], default="room", required=True)
    capacity = fields.Integer(default=1)
    active = fields.Boolean(default=True)
