/** @odoo-module **/

import {attr, one} from "@mail/model/model_field";
import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "Message",
    fields: {
        broker_type: attr(),
        broker_notifications: attr(),
        broker_channel_data: attr(),
        brokerThread: one("Thread", {inverse: "messagesAsBrokerThread"}),
    },
    modelMethods: {
        convertData(data) {
            const data2 = this._super(data);
            data2.broker_type = data.broker_type;
            data2.broker_channel_data = data.broker_channel_data;
            data2.broker_notifications = data.broker_notifications;
            if (
                data.broker_thread_data &&
                Object.keys(data.broker_thread_data).length > 0
            ) {
                /* Const brokerThreadData = data.broker_thread_data
                if ('record_name' in data && data.record_name) {
                    brokerThreadData.name = data.record_name;
                }
                if ('res_model_name' in data && data.res_model_name) {
                    brokerThreadData.model_name = data.res_model_name;
                }
                if ('module_icon' in data) {
                    brokerThreadData.moduleIcon = data.module_icon;
                }*/
                data2.brokerThread = data.broker_thread_data;
            }
            return data2;
        },
    },
});
