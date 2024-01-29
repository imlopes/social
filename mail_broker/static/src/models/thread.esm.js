/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "Thread",
    fields: {
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
