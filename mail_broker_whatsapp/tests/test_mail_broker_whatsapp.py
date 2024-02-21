# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.mail_broker.tests.common import MailBrokerTestCase


@tagged("-at_install", "post_install")
class TestMailBrokerTelegram(MailBrokerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.webhook = "demo_hook"
        cls.broker = cls.env["mail.broker"].create(
            {
                "name": "broker",
                "broker_type": "whatsapp",
                "token": "token",
                "whatsapp_security_key": "key",
                "webhook_secret": "MY-SECRET",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Partner", "mobile": "+34 600 000 000"}
        )
        cls.password = "my_new_password"
        cls.message_01 = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "1234",
                                    "phone_number_id": "1234",
                                },
                                "contacts": [
                                    {"profile": {"name": "NAME"}, "wa_id": "1234"}
                                ],
                                "messages": [
                                    {
                                        "from": "1234",
                                        "id": "wamid.ID",
                                        "timestamp": "1234",
                                        "text": {"body": "MESSAGE_BODY"},
                                        "type": "text",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    def test_webhook_management(self):
        self.broker.webhook_key = self.webhook
        self.broker.flush()
        self.assertTrue(self.broker.can_set_webhook)
        self.broker.set_webhook()
        self.assertEqual(self.broker.integrated_webhook_state, "pending")
        self.broker.remove_webhook()
        self.assertFalse(self.broker.integrated_webhook_state)
        self.broker.set_webhook()
        self.assertEqual(self.broker.integrated_webhook_state, "pending")
        self.url_open(
            "/broker/{}/{}/update?hub.verify_token={}&hub.challenge={}".format(
                self.broker.broker_type,
                self.webhook,
                self.broker.whatsapp_security_key + "12",
                "22",
            ),
        )
        self.assertEqual(self.broker.integrated_webhook_state, "pending")
        self.integrate_webhook()
        self.assertEqual(self.broker.integrated_webhook_state, "integrated")
        self.broker.remove_webhook()
        self.assertFalse(self.broker.integrated_webhook_state)

    def integrate_webhook(self):
        self.url_open(
            "/broker/{}/{}/update?hub.verify_token={}&hub.challenge={}".format(
                self.broker.broker_type,
                self.webhook,
                self.broker.whatsapp_security_key,
                "22",
            ),
        )

    def set_message(self, message, webhook, headers=True):
        data = json.dumps(message)
        headers_dict = {"Content-Type": "application/json"}
        if headers:
            headers_dict["x-hub-signature-256"] = (
                "sha256=%s"
                % hmac.new(
                    self.broker.webhook_secret.encode(),
                    data.encode(),
                    hashlib.sha256,
                ).hexdigest()
            )
        self.url_open(
            "/broker/{}/{}/update".format(self.broker.broker_type, webhook),
            data=data,
            headers=headers_dict,
        )

    def test_post_message(self):
        self.broker.webhook_key = self.webhook
        self.broker.set_webhook()
        self.integrate_webhook()
        self.set_message(self.message_01, self.webhook)
        chat = self.env["mail.channel"].search([("broker_id", "=", self.broker.id)])
        self.assertTrue(chat)
        self.assertTrue(chat.message_ids)

    def test_post_no_signature_no_message(self):
        self.broker.webhook_key = self.webhook
        self.broker.set_webhook()
        self.integrate_webhook()
        self.set_message(self.message_01, self.webhook, False)
        self.assertFalse(
            self.env["mail.channel"].search([("broker_id", "=", self.broker.id)])
        )

    def test_post_wrong_signature_no_message(self):
        self.broker.webhook_key = self.webhook
        self.broker.set_webhook()
        self.integrate_webhook()
        data = json.dumps(self.message_01)
        headers = {
            "Content-Type": "application/json",
            "x-hub-signature-256": (
                "sha256=1234%s"
                % hmac.new(
                    self.broker.webhook_secret.encode(),
                    data.encode(),
                    hashlib.sha256,
                ).hexdigest()
            ),
        }
        self.url_open(
            "/broker/{}/{}/update".format(self.broker.broker_type, self.webhook),
            data=data,
            headers=headers,
        )
        self.assertFalse(
            self.env["mail.channel"].search([("broker_id", "=", self.broker.id)])
        )

    def no_test_compose(self):
        self.broker.webhook_key = self.webhook
        self.broker.set_webhook()
        self.integrate_webhook()
        composer = self.env["whatsapp.composer"].create(
            {
                "res_model": self.partner._name,
                "res_id": self.partner.id,
                "number_field_name": "mobile",
            }
        )
        composer.action_view_whatsapp()
        channel = self.env["mail.channel"].search([("broker_id", "=", self.broker.id)])
        self.assertTrue(channel)
        self.assertFalse(channel.message_ids)
        with self.assertRaises(UserError):
            composer.action_send_whatsapp()
        composer.body = "DEMO"
        with patch("requests.post") as post_mock:
            post_mock.return_value = MagicMock()
            composer.action_send_whatsapp()
            post_mock.assert_called()
        channel.refresh()
        self.assertTrue(channel.message_ids)
