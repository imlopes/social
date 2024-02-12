# Copyright 2024 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models


class MailMessage(models.Model):

    _inherit = "mail.message"

    broker_unread = fields.Boolean(default=False)
    broker_type = fields.Selection(
        selection=lambda r: r.env["mail.broker"]._fields["broker_type"].selection
    )
    broker_notification_ids = fields.One2many(
        "mail.message.broker", inverse_name="mail_message_id"
    )
    broker_notifications = fields.Json(compute="_compute_broker_notifications")
    broker_channel_ids = fields.Many2many(
        "res.partner.broker.channel", compute="_compute_broker_channel_ids"
    )
    broker_channel_data = fields.Json(compute="_compute_broker_channel_ids")
    broker_message_ids = fields.One2many(
        "mail.message", inverse_name="broker_message_id"
    )
    broker_message_id = fields.Many2one("mail.message")

    @api.depends("notification_ids", "broker_message_ids")
    def _compute_broker_channel_ids(self):
        for record in self:
            channels = record.notification_ids.res_partner_id.broker_channel_ids.filtered(
                lambda r: (r.broker_token, r.broker_id.id)
                not in [
                    (
                        notification.channel_id.token,
                        notification.channel_id.broker_id.id,
                    )
                    for notification in record.broker_message_ids.broker_notification_ids
                ]
            )
            record.broker_channel_ids = channels
            record.broker_channel_data = {
                "channels": channels.ids,
                "partners": channels.partner_id.ids,
            }

    @api.depends("broker_notification_ids", "broker_notification_ids.state")
    def _compute_broker_notifications(self):
        for record in self:
            broker_notification = defaultdict(
                lambda: {"total": 0, "error": 0, "sent": 0, "outgoing": 0}
            )
            for notification in (
                record.broker_notification_ids
                | record.broker_message_ids.broker_notification_ids
            ):
                broker_notification[notification.channel_id.broker_id.broker_type][
                    "total"
                ] += 1
                if notification.state == "exception":
                    broker_notification[notification.channel_id.broker_id.broker_type][
                        "error"
                    ] += 1
                if notification.state == "sent":
                    broker_notification[notification.channel_id.broker_id.broker_type][
                        "sent"
                    ] += 1
                if notification.state == "outgoing":
                    broker_notification[notification.channel_id.broker_id.broker_type][
                        "outgoing"
                    ] += 1
            record.broker_notifications = dict(broker_notification)

    @api.depends("broker_notification_ids")
    def _compute_broker_channel_id(self):
        for rec in self:
            if rec.broker_notification_ids:
                rec.broker_channel_id = rec.broker_notification_ids[0].channel_id

    def set_message_done(self):
        # We need to set it as sudo in order to avoid collateral damages.
        # In fact, it is done with sudo on the original method
        self.sudo().filtered(lambda r: r.broker_unread).write({"broker_unread": False})
        return super().set_message_done()

    def _get_message_format_fields(self):
        result = super()._get_message_format_fields()
        result.append("broker_type")
        result.append("broker_notifications")
        result.append("broker_channel_data")
        return result
