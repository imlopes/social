/** @odoo-module **/

import {clear} from "@mail/model/model_field_command";
import {one} from "@mail/model/model_field";
import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "DiscussSidebarCategory",
    fields: {
        discussAsBroker: one("Discuss", {
            identifying: true,
            inverse: "categoryBroker",
        }),
        hasAddCommand: {
            compute() {
                if (this.discussAsBroker) {
                    return true;
                }
                return this._super();
            },
        },
        autocompleteMethod: {
            compute() {
                if (this.discussAsBroker) {
                    return "broker";
                }
                return this._super();
            },
        },
        newItemPlaceholderText: {
            compute() {
                if (this.discussAsBroker) {
                    return this.env._t("Find a broker channel...");
                }
                return this._super();
            },
        },
        isServerOpen: {
            compute() {
                // There is no server state for non-users (guests)
                if (!this.messaging.currentUser) {
                    return clear();
                }
                if (!this.messaging.currentUser.res_users_settings_id) {
                    return clear();
                }
                if (this.discussAsBroker) {
                    return true;
                }
                return this._super();
            },
        },
        name: {
            compute() {
                if (this.discussAsBroker) {
                    return this.env._t("Broker");
                }
                return this._super();
            },
        },

        categoryItemsOrderedByLastAction: {
            compute() {
                if (this.discussAsBroker) {
                    return this.categoryItems;
                }
                return this._super();
            },
        },
        orderedCategoryItems: {
            compute() {
                if (this.discussAsBroker) {
                    return this.categoryItemsOrderedByLastAction;
                }
                return this._super();
            },
        },
        supportedChannelTypes: {
            compute() {
                if (this.discussAsBroker) {
                    return ["broker"];
                }
                return this._super();
            },
        },
    },
    recordMethods: {
        onAddItemAutocompleteSource(req, res) {
            if (this.autocompleteMethod === "broker") {
                this.messaging.discuss.handleAddBrokerAutocompleteSource(req, res);
            }
            return this._super(...arguments);
        },

        onAddItemAutocompleteSelect(ev, ui) {
            if (this.autocompleteMethod === "broker") {
                return this.messaging.discuss.handleAddBrokerAutocompleteSelect(ev, ui);
            }
            return this._super(...arguments);
        },
    },
});
