/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

patch(ControlPanel.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.rpc = useService('rpc');
        this.state = useState({
            viewName: "",
            info: {
                new_development: { label: "New Development", count: 0 },
                eliminated: { label: "Eliminated", count: 0 },
                production_available: { label: "Production Available", count: 0 }
            }
        });
        
        if (this.env.config.viewId) {
            this.orm.call(
                "ir.ui.view",
                "read",
                [[this.env.config.viewId], ["name"]]
            ).then(view => {
                if (view && view[0]) {
                    this.state.viewName = view[0].name;
                    console.log("View name set to:", this.state.viewName);
                }
            });

            this.rpc('/garment/sample/general_info', {})
                .then((info) => {
                    console.log("Received general info:", info);
                    if (info) {
                        this.state.info = info;
                        console.log("Updated state info:", this.state.info);
                    }
                })
                .catch(error => {
                    console.error("Error fetching general info:", error);
                });
        }
    },
}); 