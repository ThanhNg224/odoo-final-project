/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DropdownHandler {
    setup() {
        this.actionService = useService("action");
    }

    onDropdownItemClick(ev) {
        const button = ev.currentTarget;
        const action = button.getAttribute('name');
        if (action) {
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                name: action,
                res_model: 'garment.sample',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            });
        }
    }
}

registry.category("actions").add("dropdown_handler", DropdownHandler); 