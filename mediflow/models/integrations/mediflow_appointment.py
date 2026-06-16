# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class MediflowAppointment(models.Model):
    """Telehealth links and patient reminders via the integration service."""

    _inherit = "mediflow.appointment"

    mf_video_url = fields.Char(string="Telehealth Link", copy=False, readonly=True)

    def action_mf_generate_video(self):
        self.ensure_one()
        result = self.env["mediflow.integration.service"].create_video_room(
            label=self.name or "visit")
        if result.get("ok"):
            self.mf_video_url = result["url"]
        return True

    def action_mf_send_reminder(self):
        """Send an SMS reminder to the patient. Used manually or by automation
        (e.g. targeting high no-show risk appointments)."""
        service = self.env["mediflow.integration.service"]
        sent = 0
        for appt in self:
            phone = appt.patient_id.phone
            if not phone:
                continue
            body = _("Reminder: your appointment %(ref)s is on %(when)s. "
                     "Reply to reschedule.") % {
                "ref": appt.name, "when": fields.Datetime.to_string(appt.start)}
            if appt.mf_video_url:
                body += _(" Join online: %s") % appt.mf_video_url
            res = service.send_sms(phone, body, patient=appt.patient_id)
            if res.get("ok"):
                sent += 1
        if not sent:
            raise UserError(_(
                "No reminder was sent. Check that an active SMS integration is "
                "configured and the patient has a phone number."))
        return True
