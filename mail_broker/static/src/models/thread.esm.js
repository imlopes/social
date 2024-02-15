/** @odoo-module **/

import {many} from "@mail/model/model_field";
import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "Thread",
    fields: {
        messagesAsBrokerThread: many("Message", {
            inverse: "brokerThread",
            isCausal: true,
        }),
        hasInviteFeature: {
            compute() {
                if (this.channel && this.channel.channel_type === "broker") {
                    return true;
                }
                return this._super();
            },
        },
        hasMemberListFeature: {
            compute() {
                if (this.channel && this.channel.channel_type === "broker") {
                    return true;
                }
                return this._super();
            },
        },
        isChatChannel: {
            compute() {
                if (this.channel && this.channel.channel_type === "broker") {
                    return true;
                }
                return this._super();
            },
        },
    },
});
