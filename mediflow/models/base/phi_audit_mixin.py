# -*- coding: utf-8 -*-
from odoo import models


class PhiAuditMixin(models.AbstractModel):
    """Adds append-only audit on create/write/unlink for PHI-bearing models.

    Concrete models may set ``_phi_audit_fields`` to limit which field changes are
    recorded (defaults to all tracked-relevant fields). The patient partner is
    resolved through ``_phi_patient_id`` for cross-referencing in the audit log.
    """

    _name = "mediflow.phi.audit.mixin"
    _description = "MEDIFLOW PHI Audit Mixin"

    _phi_audit_fields = None  # None -> audit all changed fields

    def _phi_patient_id(self):
        for fname in ("patient_id", "partner_id"):
            if fname in self._fields and self[fname]:
                rec = self[fname]
                return rec.partner_id.id if "partner_id" in rec._fields else rec.id
        return False

    def _phi_company_id(self):
        if "company_id" in self._fields and self.company_id:
            return self.company_id.id
        return self.env.company.id

    def _phi_log(self, action, field_changes=None):
        if "mediflow.audit.log" not in self.env:
            return
        for record in self:
            record.env["mediflow.audit.log"].log(
                model=record._name,
                res_id=record.id,
                action=action,
                patient_id=record._phi_patient_id(),
                field_changes=field_changes,
                company_id=record._phi_company_id(),
            )

    def read(self, fields=None, load="_classic_read"):
        result = super().read(fields=fields, load=load)
        if self.env.context.get("phi_audit_read") and not self.env.context.get("phi_no_audit"):
            self._phi_log("read")
        return result

    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("phi_no_audit"):
            records._phi_log("create")
        return records

    def write(self, vals):
        if not self.env.context.get("phi_no_audit"):
            audited = self._phi_audit_fields
            tracked = {k: v for k, v in vals.items()
                       if audited is None or k in audited}
            if tracked:
                for record in self:
                    changes = {k: [record[k] and str(record[k]), str(tracked[k])]
                               for k in tracked}
                    record._phi_log("write", field_changes=changes)
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("phi_no_audit"):
            self._phi_log("unlink")
        return super().unlink()
