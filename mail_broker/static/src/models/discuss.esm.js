/** @odoo-module **/

import {one} from "@mail/model/model_field";
import {registerPatch} from "@mail/model/model_core";

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
    recordMethods: {
        async handleAddBrokerAutocompleteSource(req, res) {
            this.discussView.update({addingChannelValue: req.term});
            const threads = await this.messaging.models.Thread.searchBrokersToOpen({
                limit: 10,
                searchTerm: req.term,
            });
            const items = threads.map((thread) => {
                const escapedName = escape(thread.name);
                return {
                    id: thread.id,
                    label: escapedName,
                    value: escapedName,
                };
            });
            res(items);
        },
        async handleAddBrokerAutocompleteSelect(ev, ui) {
            // Necessary in order to prevent AutocompleteSelect event's default
            // behaviour as html tags visible for a split second in text area
            ev.preventDefault();
            const channel = this.messaging.models.Thread.insert({
                id: ui.item.id,
                model: "mail.channel",
            });
            await channel.join();
            // Channel must be pinned immediately to be able to open it before
            // the result of join is received on the bus.
            channel.update({isServerPinned: true});
            channel.open();
        },
    },
});
