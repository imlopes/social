# Copyright 2024 Dixmit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.http import Controller, request, route


class BrokerController(Controller):
    @route(
        "/broker/<string:usage>/<string:token>/update",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def post_update(self, usage, token, *args, **kwargs):
        jsonrequest = request.dispatcher.jsonrequest
        bot_data = request.env["mail.broker"]._get_broker(
            token, broker_type=usage, state="integrated", **jsonrequest
        )
        if not bot_data:
            return {}
        dispatcher = request.env["mail.broker.%s" % usage].with_user(
            bot_data["webhook_user_id"]
        )
        if not dispatcher._verify_update(bot_data, jsonrequest):
            return {}
        broker = dispatcher.env["mail.broker"].browse(bot_data["id"])
        dispatcher._receive_update(broker.with_context(notify_broker=True), jsonrequest)
        return False
