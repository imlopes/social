# Copyright 2024 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.modules.module import get_resource_path

from odoo.addons.base.models.avatar_mixin import get_hsl_from_seed


class MailChannel(models.Model):

    _inherit = "mail.channel"

    @api.returns("mail.message.broker", lambda value: value.id)
    def telegram_message_post_broker(self, body=False, **kwargs):
        return self.message_post_broker(body=body, broker_type="telegram", **kwargs)

    def _generate_avatar_broker(self):
        if self.broker_id.broker_type == "telegram":
            path = get_resource_path(
                "mail_broker_telegram", "static/description", "telegram.svg"
            )
            with open(path, "r") as f:
                avatar = f.read()

            bgcolor = get_hsl_from_seed(self.uuid)
            avatar = avatar.replace("fill:#875a7b", f"fill:{bgcolor}")
            return avatar
        return super()._generate_avatar_broker()
