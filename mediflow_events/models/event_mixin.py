# -*- coding: utf-8 -*-
import json

from odoo import models


class EventMixin(models.AbstractModel):
    """Gives any model a single, audited way to raise domain events.

    Usage in a concrete model::

        self._emit_event("appointment.booked", {"id": self.id})

    The event is persisted durably (``mediflow.event``) inside the current
    transaction and a live ``bus.bus`` notification is pushed for connected UIs.
    Outbound webhook delivery happens asynchronously via the delivery cron.
    """

    _name = "mediflow.event.mixin"
    _description = "MEDIFLOW Event Emitter Mixin"

    def _emit_event(self, name, payload=None, version="1"):
        payload = dict(payload or {})
        payload.setdefault("model", self._name)
        if len(self) == 1 and self.id:
            payload.setdefault("id", self.id)
        company_id = (self.company_id.id
                      if "company_id" in self._fields and self.company_id
                      else self.env.company.id)
        event = self.env["mediflow.event"].emit(
            name=name, payload=payload, source_model=self._name,
            source_res_id=self.id if len(self) == 1 else False,
            version=version, company_id=company_id,
        )
        self._emit_bus(name, payload, company_id)
        return event

    def _emit_bus(self, name, payload, company_id):
        """Push a live notification on a clinic-scoped channel."""
        channel = (self.env.cr.dbname, "mediflow.event", company_id)
        try:
            self.env["bus.bus"]._sendone(channel, "mediflow_event",
                                         {"name": name, "payload": payload})
        except Exception:  # noqa: BLE001 - live notification is best-effort
            pass
