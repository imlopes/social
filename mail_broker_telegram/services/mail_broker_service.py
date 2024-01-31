# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import logging
import mimetypes
import traceback
from io import BytesIO, StringIO

from odoo import _
from odoo.http import request
from odoo.tools import html2plaintext
from odoo.tools.mimetypes import guess_mimetype

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

try:
    import asyncio

    import telegram
    from lottie.exporters import exporters
    from lottie.importers import importers
except (ImportError, IOError) as err:
    _logger.debug(err)


class MailBrokerTelegramService(Component):
    _inherit = "mail.broker.base.service"
    _name = "mail.broker.telegram.service"
    _usage = "telegram"
    _description = "Telegram Broker services"

    def _get_telegram_bot(self, token=False):
        return telegram.Bot(token or self.collection.token)

    def _set_webhook(self):
        bot = self._get_telegram_bot()
        asyncio.run(
            bot.setWebhook(
                url=self.collection.webhook_url,
                api_kwargs={"secret_token": self.collection.webhook_secret},
            )
        )
        return super()._set_webhook()

    async def _remove_webhook_telegram(self):
        bot = self._get_telegram_bot()
        await bot.initialize()
        webhookinfo = await bot.get_webhook_info()
        if webhookinfo.url:
            await bot.delete_webhook(drop_pending_updates=False)

    def _remove_webhook(self):
        asyncio.run(self._remove_webhook_telegram())
        return super()._remove_webhook()

    def _verify_update(self, bot_data, kwargs):
        if not bot_data["webhook_secret"]:
            return True
        return (
            request.httprequest.headers.get("X-Telegram-Bot-Api-Secret-Token")
            == bot_data["webhook_secret"]
        )

    def _get_channel_vals(self, broker, token, update):
        result = super()._get_channel_vals(broker, token, update)
        names = []
        for name in [
            update.message.chat.first_name or False,
            update.message.chat.last_name or False,
            update.message.chat.description or False,
            update.message.chat.title or False,
        ]:
            if name:
                names.append(name)
        result["name"] = " ".join(names)
        result["anonymous_name"] = " ".join(names)
        return result

    def _preprocess_update(self, broker, update):
        for entity in update.message.entities:
            if not entity.offset == 0:
                continue
            if not entity.type == "bot_command":
                continue
            command = update.message.parse_entity(entity).split("/")[1]
            if hasattr(self, "_command_%s" % (command)):
                return getattr(self, "_command_%s" % (command))(broker, update)
        return False

    def _command_start(self, broker, update):
        if (
            not broker.has_new_channel_security
            or update.message.text == "/start %s" % broker.telegram_security_key
        ):
            return self._get_channel(broker, update.message.chat_id, update, True)
        return True

    def _receive_update(self, broker, update):
        telegram_update = telegram.Update.de_json(
            update, self._get_telegram_bot(token=broker.token)
        )
        if self._preprocess_update(broker, telegram_update):
            return
        chat = self._get_channel(
            broker, telegram_update.message.chat_id, telegram_update
        )
        if not chat:
            return
        return self._process_update(chat, telegram_update)

    def _telegram_sticker_input_options(self):
        return {}

    def _telegram_sticker_output_options(self):
        return {}

    def _get_telegram_attachment_name(self, attachment):
        if hasattr(attachment, "title"):
            if attachment.title:
                return attachment.title
        if hasattr(attachment, "file_name"):
            if attachment.file_name:
                return attachment.file_name
        if isinstance(attachment, telegram.Sticker):
            return attachment.set_name or attachment.emoji or "sticker"
        if isinstance(attachment, telegram.Contact):
            return attachment.first_name
        return attachment.file_id

    async def _process_telegram_attachment(self, attachment):
        if isinstance(attachment, tuple):
            attachment = attachment[-1]
            # That might happen with images, we will get the last one as it is the bigger one.
        if isinstance(
            attachment,
            (
                telegram.Game,
                telegram.Invoice,
                telegram.Location,
                telegram.SuccessfulPayment,
                telegram.Venue,
            ),
        ):
            return
        if isinstance(attachment, telegram.Contact):
            data = attachment.vcard.encode("utf-8")
        else:
            file = await attachment.get_file()
            data = bytes(await file.download_as_bytearray())
        file_name = self._get_telegram_attachment_name(attachment)
        if isinstance(attachment, telegram.Sticker):
            suf = "tgs"
            for p in importers:
                if suf in p.extensions:
                    importer = p
                    break
            exporter = exporters.get("gif")
            inpt = BytesIO(data)
            an = importer.process(inpt, **self._telegram_sticker_input_options())
            output_options = self._telegram_sticker_output_options()
            fps = output_options.pop("fps", False)
            if fps:
                an.frame_rate = fps
            output = BytesIO()
            exporter.process(an, output, **output_options)
            data = output.getvalue()
        mimetype = guess_mimetype(data)
        return (
            "{}{}".format(file_name, mimetypes.guess_extension(mimetype)),
            base64.b64encode(data).decode("utf-8"),
            mimetype,
        )

    def _process_update(self, chat, update):
        chat.ensure_one()
        body = ""
        attachments = []
        if update.message.text_html:
            body = update.message.text_html
        if update.message.effective_attachment:
            effective_attachment = update.message.effective_attachment
            if isinstance(effective_attachment, list):
                current_attachment = effective_attachment[0]
                for attachment in effective_attachment[1:]:
                    if getattr(attachment, "file_size", 0) > getattr(
                        current_attachment, "file_size", 0
                    ):
                        current_attachment = attachment
                effective_attachment = current_attachment
            if isinstance(effective_attachment, telegram.Location):
                body += (
                    '<a target="_blank" href="https://www.google.com/'
                    'maps/search/?api=1&query=%s,%s">Location</a>'
                    % (
                        effective_attachment.latitude,
                        effective_attachment.longitude,
                    )
                )
            attachment_data = asyncio.run(
                self._process_telegram_attachment(effective_attachment)
            )
            if attachment_data:
                attachments.append(attachment_data)
        if len(body) > 0 or attachments:
            return chat.message_post_broker(
                body=body,
                author=self._get_author(chat.broker_id, update),
                broker_type="telegram",
                date=update.message.date.replace(tzinfo=None),
                message_id=update.message.message_id,
                subtype="mt_comment",
                attachments=attachments,
            )

    async def _send_telegram(
        self, record, auto_commit=False, raise_exception=False, parse_mode=False
    ):
        bot = self._get_telegram_bot()
        await bot.initialize()
        chat = await bot.get_chat(record.channel_id.token)
        message = False
        if record.body:
            message = await chat.send_message(
                html2plaintext(record.body), parse_mode=parse_mode
            )
        for attachment in record.attachment_ids:
            if attachment.mimetype.split("/")[0] == "image":
                new_message = await chat.send_photo(
                    BytesIO(base64.b64decode(attachment.datas))
                )
            else:
                new_message = await chat.send_document(
                    BytesIO(base64.b64decode(attachment.datas)),
                    filename=attachment.name,
                )
            if not message:
                message = new_message
        return message

    def _send(self, record, auto_commit=False, raise_exception=False, parse_mode=False):
        message = False
        try:
            asyncio.run(
                self._send_telegram(
                    record,
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    parse_mode=parse_mode,
                )
            )
        except Exception as exc:
            buff = StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())
            if raise_exception:
                raise MailDeliveryException(
                    _("Unable to send the telegram message"), exc
                ) from None
            else:
                _logger.warning(
                    "Issue sending message with id {}: {}".format(record.id, exc)
                )
                record.write({"state": "exception", "failure_reason": exc})
        if message:
            record.write(
                {
                    "state": "sent",
                    "message_id": message.message_id,
                    "failure_reason": False,
                }
            )
        if auto_commit is True:
            # pylint: disable=invalid-commit
            self.env.cr.commit()

    def _get_author_vals(self, broker, update):
        names = []
        for name in [
            update.message.from_user.first_name or False,
            update.message.from_user.last_name or False,
        ]:
            if name:
                names.append(name)
        return {
            "name": " ".join(names),
            "broker_id": broker.id,
            "broker_token": str(update.message.from_user.id),
        }

    def _get_author(self, broker, update):
        author_id = update.message.from_user.id
        if author_id:
            broker_partner = self.env["res.partner.broker.channel"].search(
                [("broker_id", "=", broker.id), ("broker_token", "=", str(author_id))]
            )
            if broker_partner:
                return broker_partner.partner_id
            guest = self.env["mail.guest"].search(
                [("broker_id", "=", broker.id), ("broker_token", "=", str(author_id))]
            )
            if guest:
                return guest
            return self.env["mail.guest"].create(self._get_author_vals(broker, update))

        return super()._get_author(broker, update)
