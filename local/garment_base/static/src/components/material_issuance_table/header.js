/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component, useEffect, useRef, useState } from "@odoo/owl";
import { MaterialIssuanceDialog } from "./dialog";
import { useService } from "@web/core/utils/hooks";
import { extractFieldsFromArchInfo } from "@web/model/relational_model/utils";

export class MaterialIssuanceTableHeader extends Component {
    static template = "garment.material_issuance_table_header";
    static components = { MaterialIssuanceDialog };
    static props = {
        ...standardWidgetProps,
        close: { type: Function },
        confirm: { type: Function },
        record: { type: Object },
        fields: { type: Object },
        archInfo: { type: Object, optional: true },
    };

    setup() {
        super.setup();
        // console.log("Fields", this.props.record);
        this.dialog = useService("dialog");
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            totalItems: 0,
        });
        
        this.updateTotalItems();
    }

    updateTotalItems() {
        const materialIssuanceIds = this.props.record.data.material_issuance_ids;
        this.state.totalItems = materialIssuanceIds ? materialIssuanceIds.length : 0;
    }

    onOpenDialog() {
        this.dialog.add(MaterialIssuanceDialog, {
            close: () => this.dialog.remove(),
            confirm: (data) => this.onConfirmDialog(data),
            record: this.props.record
        });
    }

    async onConfirmDialog(data) {
        try {
            // Validate data before sending
            if (!data.material_id || !data.color_id) {
                throw new Error("Material ID and Color ID are required");
            }

            let from_model = "";
            switch(this.props.record.resModel) {
                case 'garment.sample':
                    from_model = 'sample';
                    break;
                case 'garment.order':
                    from_model = 'order';
                    break;
                case 'production.order':
                    from_model = 'production';
                    break;
                case 'garment.inventory.material':
                    from_model = 'material';
                    break;
                default:
                    from_model = 'other';
            }


            // Create MaterialReceiptLine record
            // console.log("Data to create material issuance record: ", data);
            const createData = {
                material_id: data.material_id,
                color_id: data.color_id,
                type: data.type,
                used_quantity: data.used_quantity,
                defective_quantity: data.defective_quantity,
                unit_price: data.unit_price,
                receiving_company: data.receiving_company,
                remark: data.remark,
                item_type: 'material',
                from_type: from_model,
                item_id: this.props.record.resId.toString(),
                publisher: this.props.record.evalContext.uid,
                publish_date: new Date().toISOString().split('T')[0],
                total_price: data.total_price,
            };

            // console.log("Sending to backend:", createData);

            const materialReceiptLine = await this.rpc("/web/dataset/call_kw", {
                model: "garment.receipt.line",
                method: "create",
                args: [createData],
                kwargs: {},
            });

            // console.log("Created material receipt line:", materialReceiptLine);

            // Refresh the field to show the new record
            await this.props.record.load();
            this.updateTotalItems();

            // Show success notification
            this.notification.add(_t("Material issuance record created successfully"), {
                type: "success",
                sticky: false,
            });

        } catch (error) {
            console.error("Error creating material issuance record:", error);
            
            // Extract more detailed error message
            let errorMessage = "Unknown error occurred";
            if (error.data && error.data.message) {
                errorMessage = error.data.message;
            } else if (error.message) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }

            this.notification.add(_t("Failed to create material issuance record: %s", errorMessage), {
                type: "danger",
                sticky: true,
            });
        }
    }
}

export const materialIssuanceTableHeader = {
    component: MaterialIssuanceTableHeader,
    displayName: "Material Issuance Table Header",
    fieldDependencies: [
        { name: "material_issuance_ids", type: "one2many" },
    ],
};
registry.category("view_widgets").add("material_issuance_widget", materialIssuanceTableHeader);
