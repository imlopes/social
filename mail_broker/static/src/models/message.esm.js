/** @odoo-module **/

import {attr} from "@mail/model/model_field";
import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "Message",
    fields: {
        broker_type: attr(),
        broker_notifications: attr(),
        broker_channel_data: attr(),
    },
    modelMethods: {
        convertData(data) {
            const data2 = this._super(data);
            data2.broker_type = data.broker_type;
            data2.broker_channel_data = data.broker_channel_data;
            data2.broker_notifications = data.broker_notifications;
            return data2;
        },
    },
});
