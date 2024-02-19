# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMessageBrokerSend(models.TransientModel):

    _name = "mail.message.broker.send"
    _description = "Send Message through broker"

    message_id = fields.Many2one("mail.message", required=True)
    partner_id = fields.Many2one("res.partner", required=True)
    broker_channel_id = fields.Many2one(
        "res.partner.broker.channel",
        required=True,
    )

    def send(self):
        chat_id = self.broker_channel_id.broker_id._get_channel_id(
            self.broker_channel_id.broker_token
        )
        channel = self.env["mail.channel"].browse(chat_id)
        channel.message_post(**self._get_message_vals())
        self.env["mail.notification"].create(
            {
                "notification_status": "sent",
                "mail_message_id": self.message_id.id,
                "broker_channel_id": channel.id,
                "notification_type": "broker",
                "broker_type": self.broker_channel_id.broker_id.broker_type,
            }
        )
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "mail.message/insert",
            {
                "id": self.message_id.id,
                "notifications": self.message_id.sudo()
                .notification_ids._filtered_for_web_client()
                ._notification_format(),
            },
        )
        return {}

    def _get_message_vals(self):
        return {
            "body": self.message_id.body,
            "attachment_ids": self.message_id.attachment_ids.ids,
            "subtype_id": self.message_id.subtype_id.id,
            "author_id": self.env.user.partner_id.id,
            "broker_message_id": self.message_id.id,
            "message_type": "comment",
        }
