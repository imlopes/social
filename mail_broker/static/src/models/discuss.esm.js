/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";
import {one} from "@mail/model/model_field";

registerPatch({
    name: "Discuss",
    fields: {
        /**
         * Discuss sidebar category for `livechat` channel threads.
         */
        categoryBroker: one("DiscussSidebarCategory", {
            default: {},
            inverse: "discussAsBroker",
        }),
    },
});
