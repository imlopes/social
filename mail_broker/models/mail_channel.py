# Copyright 2024 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime
from xmlrpc.client import DateTime

from odoo import api, fields, models


class MailChannel(models.Model):
    _inherit = "mail.channel"

    token = fields.Char()
    anonymous_name = fields.Char()  # Same field we will use on im_livechat
    broker_id = fields.Many2one("mail.broker")
    broker_message_ids = fields.One2many(
        "mail.message.broker",
        inverse_name="channel_id",
    )
    channel_type = fields.Selection(
        selection_add=[("broker", "Broker")], ondelete={"broker": "set default"}
    )
    broker_token = fields.Char(related="broker_id.token", store=True, required=False)

    def _generate_avatar_broker(self):
        # We will use this function to set a default avatar on each module
        return False

    def _generate_avatar(self):
        if self.channel_type not in ("broker"):
            return super()._generate_avatar()
        avatar = self._generate_avatar_broker()
        if not avatar:
            return False
        return base64.b64encode(avatar.encode())

    def _broker_message_post_vals(
        self,
        body,
        subtype_id=False,
        author=False,
        email_from=False,
        date=False,
        message_id=False,
        **kwargs
    ):
        if not subtype_id:
            subtype = kwargs.get("subtype") or "mt_note"
            if "." not in subtype:
                subtype = "mail.%s" % subtype
            subtype_id = self.env.ref(subtype).id
        vals = {
            "channel_id": self.id,
            "body": body,
            "subtype_id": subtype_id,
            "model": self._name,
            "res_id": self.id,
            "broker_type": self.broker_id.broker_type,
        }
        if author and author._name == "res.partner":
            vals["author_id"] = author.id
            vals["email_from"] = email_from
        elif author and author._name == "mail.guest":
            vals["author_guest_id"] = author.id
            vals["email_from"] = author.display_name
            vals["author_id"] = False
        else:
            vals["email_from"] = email_from
            vals["author_id"] = False
        if date:
            if isinstance(date, DateTime):
                date = datetime.strptime(str(date), "%Y%m%dT%H:%M:%S")
            vals["date"] = date
        if message_id:
            vals["message_id"] = message_id
        vals["broker_unread"] = kwargs.get("broker_unread", False)
        vals["attachment_ids"] = []
        for attachment_id in kwargs.get("attachment_ids", []):
            vals["attachment_ids"].append((4, attachment_id))
        for name, content, mimetype in kwargs.get("attachments", []):
            vals["attachment_ids"].append(
                (
                    0,
                    0,
                    {
                        "name": name,
                        "datas": content.encode("utf-8"),
                        "type": "binary",
                        "description": name,
                        "mimetype": mimetype,
                    },
                )
            )
        return vals

    @api.returns("mail.message.broker", lambda value: value.id)
    def message_post_broker(
        self, body=False, broker_type=False, author_id=False, **kwargs
    ):
        self.ensure_one()
        if (
            not body
            and not kwargs.get("attachments")
            and not kwargs.get("attachment_ids")
        ):
            return False
        vals = self._broker_message_post_vals(
            body, broker_unread=True, email_from=self.anonymous_name, **kwargs
        )
        vals["state"] = "received"
        vals["broker_type"] = broker_type
        return self.env["mail.message.broker"].create(vals)

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, *args, **kwargs):
        message = super().message_post(*args, **kwargs)
        if self.broker_id:
            self.env["mail.message.broker"].create(
                {
                    "mail_message_id": message.id,
                    "channel_id": self.id,
                }
            ).send()
        return message

    @api.returns("mail.message.broker", lambda value: value.id)
    def broker_message_post(self, body=False, **kwargs):
        self.ensure_one()
        if not body and not kwargs.get("attachment_ids"):
            return
        message = (
            self.with_context(do_not_notify=True)
            .env["mail.message.broker"]
            .create(self._broker_message_post_vals(body, **kwargs))
        )
        message.send()
        self.env["bus.bus"].sendone(
            (self._cr.dbname, "mail.broker", message.channel_id.broker_id.id),
            {"message": message.mail_message_id.message_format()[0]},
        )
        return message

    def _message_update_content_after_hook(self, message):
        self.ensure_one()
        if self.channel_type == "broker" and message.broker_notification_ids:
            self.env[
                "mail.broker.{}".format(self.broker_id.broker_type)
            ]._update_content_after_hook(self, message)
        return super()._message_update_content_after_hook(message=message)
