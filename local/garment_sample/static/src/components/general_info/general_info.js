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
            currentModel: "",
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
                [[this.env.config.viewId], ["name", "model"]]
            ).then(view => {
                var viewName = "";
                if (view && view[0]) {
                    this.state.viewName = view[0].name;
                    this.state.currentModel = view[0].model;
                    viewName = view[0].name;
                }

                if (viewName === 'garment.sample.tree') {
                    this.rpc('/garment/sample/general_info', {})
                    .then((info) => {
                        if (info) {
                            if (info.error) {
                                console.warn("Warning fetching general info:", info.error);
                            }
                            this.state.info = info;
                        }
                    })
                    .catch(error => {
                        console.warn("Warning fetching general info:", error);
                        // Keep default values in case of error
                    });
                }
            })
            .catch(error => {
                console.warn("Warning reading view:", error);
            });
        }
    },
}); 