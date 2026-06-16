# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError, AccessError


class StateMachineMixin(models.AbstractModel):
    """Declarative state machine for MEDIFLOW lifecycle models.

    Concrete models declare:

    * ``_sm_field``        - the selection field holding the state (default ``state``)
    * ``_sm_transitions``  - ``{from_state: {to_state, ...}}`` allowed map
    * ``_sm_guards``       - optional ``{(from, to): callable(record) -> None}``; raise to block
    * ``_sm_groups``       - optional ``{(from, to): 'module.group_xmlid'}`` required group
    * ``_sm_terminal``     - states that become write-protected (immutable)

    Transitions must go through :meth:`transition`. Direct ``write`` of the state
    field outside the allowed map is rejected, and writes to terminal records are
    blocked. Every transition writes an audit entry and emits a domain event when
    the model exposes ``_emit_event``.
    """

    _name = "mediflow.state.machine.mixin"
    _description = "MEDIFLOW State Machine Mixin"

    _sm_field = "state"
    _sm_transitions = {}
    _sm_guards = {}
    _sm_groups = {}
    _sm_terminal = set()

    def transition(self, target, reason=None):
        """Perform a guarded, audited transition to ``target``."""
        field = self._sm_field
        for record in self:
            source = record[field]
            if source == target:
                continue
            allowed = record._sm_transitions.get(source, set())
            if target not in allowed:
                raise UserError(_(
                    "Illegal transition for %(model)s #%(id)s: %(src)s -> %(dst)s.",
                    model=record._name, id=record.id, src=source, dst=target,
                ))
            record._sm_check_group(source, target)
            guard = record._sm_guards.get((source, target))
            if guard:
                guard(record)
            super(StateMachineMixin, record).write({field: target})
            record._sm_after_transition(source, target, reason)
        return True

    def _sm_check_group(self, source, target):
        group = self._sm_groups.get((source, target))
        if group and not self.env.user.has_group(group):
            raise AccessError(_(
                "You are not allowed to move %(model)s from %(src)s to %(dst)s.",
                model=self._name, src=source, dst=target,
            ))

    def _sm_after_transition(self, source, target, reason):
        """Hook: audit + event emission. Override to extend, call ``super`` first."""
        patient_id = self._sm_patient_id()
        if "mediflow.audit.log" in self.env:
            self.env["mediflow.audit.log"].log(
                model=self._name,
                res_id=self.id,
                action="state",
                patient_id=patient_id,
                reason=reason,
                field_changes={self._sm_field: [source, target]},
                company_id=self._sm_company_id(),
            )
        if hasattr(self, "_emit_event"):
            event_name = "%s.%s" % (self._name.replace(".", "_"), target)
            self._emit_event(event_name, {"id": self.id, "from": source, "to": target})

    def _sm_patient_id(self):
        """Best-effort resolution of the related patient partner for audit."""
        for fname in ("patient_id", "partner_id"):
            if fname in self._fields:
                rec = self[fname]
                if rec:
                    # patient models expose partner_id; partner fields are partners already
                    return rec.partner_id.id if "partner_id" in rec._fields else rec.id
        return False

    def _sm_company_id(self):
        if "company_id" in self._fields and self.company_id:
            return self.company_id.id
        return self.env.company.id

    def write(self, vals):
        field = self._sm_field
        # Block edits to immutable/terminal records (except the audited addendum path).
        for record in self:
            if record[field] in record._sm_terminal and not self.env.context.get("sm_allow_terminal"):
                editable = set(vals) - {field}
                if editable:
                    raise UserError(_(
                        "%(model)s #%(id)s is in a terminal state (%(state)s) and is immutable.",
                        model=record._name, id=record.id, state=record[field],
                    ))
        # Reject out-of-band state changes; force callers through transition().
        if field in vals and not self.env.context.get("sm_internal"):
            for record in self:
                if record[field] != vals[field]:
                    raise UserError(_(
                        "Use the documented action to change the status of %(model)s; "
                        "direct status edits are not allowed.", model=record._name,
                    ))
        return super().write(vals)
