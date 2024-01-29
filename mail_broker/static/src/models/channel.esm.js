/** @odoo-module **/

import {attr} from "@mail/model/model_field";
import {clear} from "@mail/model/model_field_command";
import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "Channel",
    fields: {
        broker_type: attr(),
        discussSidebarCategory: {
            compute() {
                // On broker channels we must set the right category
                if (this.channel_type === "broker") {
                    return this.messaging.discuss.categoryBroker;
                }
                return this._super();
            },
        },
        correspondent: {
            compute() {
                // We will not set a correspondent on brokers, as it gets yourself.
                if (this.channel_type === "broker") {
                    return clear();
                }
                return this._super();
            },
        },
    },
});
