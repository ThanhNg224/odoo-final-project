/** @odoo-module **/
import { ListController } from '@web/views/list/list_controller';
import { listView } from '@web/views/list/list_view';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { ListRenderer } from "@web/views/list/list_renderer";
import { _t } from "@web/core/l10n/translation";
import { useState, onMounted } from "@odoo/owl";

class ReceiptListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService('action');
        this.userService = useService('user');
        this.state = useState({
            canCreate: false,
            canDelete: false,
            canDuplicate: false,
        });
        this.archInfo = this.props.archInfo;
        this.activeActions = {
            delete: false,
            duplicate: false,
        };
        onMounted(() => this.checkPermissions());
    }

    async checkPermissions() {
        const userGroups = await this.userService.hasGroup('garment_authorization.group_inventory_approval');
        this.state.canCreate = userGroups;
        this.state.canDelete = userGroups;
        this.state.canDuplicate = userGroups;
        
        // Update activeActions based on permissions
        this.activeActions = {
            delete: userGroups,
            duplicate: userGroups,
        };
    }

    onCreateButtonClick = () => {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Create Garment Receipt',
            res_model: 'garment.receipt.line',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
            context: {
                default_state: 'draft',
                create: true,
                form_view_ref: 'garment_inventory.view_garment_receipt_line_form_edit'
            }
        });
    }

    getStaticActionMenuItems() {
        const list = this.model.root;
        const isM2MGrouped = list.groupBy.some((groupBy) => {
            const fieldName = groupBy.split(":")[0];
            return list.fields[fieldName].type === "many2many";
        });
        return {
            export: {
                isAvailable: () => this.isExportEnable,
                sequence: 10,
                icon: "fa fa-upload",
                description: _t("Export"),
                callback: () => this.onExportData(),
            },
            duplicate: {
                isAvailable: () => this.activeActions.duplicate && !isM2MGrouped,
                sequence: 35,
                icon: "fa fa-clone",
                description: _t("Duplicate"),
                callback: () => this.duplicateRecords(),
            },
            delete: {
                isAvailable: () => this.activeActions.delete && !isM2MGrouped,
                sequence: 40,
                icon: "fa fa-trash-o",
                description: _t("Delete"),
                callback: () => this.onDeleteSelectedRecords(),
            },
        };
    }
}

// Register the custom list view
registry.category('views').add('receipt_tree_view', {
    ...listView,
    Controller: ReceiptListController,
    buttonTemplate: 'garment_inventory.create_button.buttons',
});
