/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

const formatters = registry.category("formatters");

class TemplateNameDialog extends Component {
    static template = xml`
        <Dialog title="'Save Template'" size="'sm'">
            <div class="p-3">
                <div class="mb-3">
                    <label class="form-label" for="templateName">Template Name</label>
                    <input
                        t-model="state.templateName"
                        type="text"
                        class="form-control"
                        id="templateName"
                        placeholder="Enter template name"/>
                </div>
            </div>
            <t t-set-slot="footer">
                <div class="text-end">
                    <button
                        type="button"
                        class="btn btn-secondary me-2"
                        t-on-click="() => props.close()">
                        Cancel
                    </button>
                    <button
                        type="button"
                        class="btn btn-primary"
                        t-on-click="onConfirm">
                        Save
                    </button>
                </div>
            </t>
        </Dialog>
    `;
    static components = { Dialog };
    static props = {
        close: Function,
        confirm: Function,
    };

    setup() {
        this.state = useState({
            templateName: '',
        });
    }

    onConfirm = () => {
        if (this.state.templateName.trim()) {
            this.props.confirm(this.state.templateName);
            this.props.close();
        }
    }
}

class TemplateSelectionDialog extends Component {
    static template = xml`
        <Dialog title="'Select Template'" size="'md'">
            <div class="p-3">
                <div class="mb-3">
                    <div class="list-group">
                        <t t-foreach="props.templates" t-as="template" t-key="template.id">
                            <button
                                type="button"
                                class="list-group-item list-group-item-action"
                                t-on-click="() => props.confirm(template)">
                                <t t-esc="template.name"/>
                            </button>
                        </t>
                    </div>
                </div>
            </div>
            <t t-set-slot="footer">
                <div class="text-end">
                    <button
                        type="button"
                        class="btn btn-secondary"
                        t-on-click="() => props.close()">
                        Cancel
                    </button>
                </div>
            </t>
        </Dialog>
    `;
    static components = { Dialog };
    static props = {
        close: Function,
        confirm: Function,
        templates: Array,
    };
}

export class QuantityListTable extends Component {
    static template = "production_management.QuantityListTable";
    static props = {
        ...standardFieldProps,
        decorations: { type: Object, optional: true },
        options: { type: Object, optional: true },
    };
    static defaultProps = {
        decorations: {},
        options: {},
    };

    setup() {
        this.rpc = useService('rpc');
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            rows: Array.isArray(this.formattedValue) ? this.formattedValue : [['Size', 'Quantity'], ['', '']],
            template_model: "production.quantity_list_template",
        });

        onWillUpdateProps((nextProps) => {
            const newArray = Array.isArray(nextProps.record.data[this.props.name]) 
                ? nextProps.record.data[this.props.name] 
                : [['Size', 'Quantity'], ['', '']];
            this.state.rows.splice(0, this.state.rows.length, ...newArray);
        });
    }

    get formattedValue() {
        const fieldDef = this.props.record.fields[this.props.name];
        const rawValue = this.props.record.data[this.props.name];
        if (fieldDef.type === 'json' || fieldDef.type === 'text') {
            try {
                return typeof rawValue === 'string'
                    ? JSON.parse(rawValue)
                    : rawValue;
            } catch {
                console.error('Invalid JSON in field', rawValue);
                return [['Size', 'Quantity'], ['', '']];
            }
        }
        const formatter = formatters.get(fieldDef.type);
        return formatter(rawValue, { selection: fieldDef.selection });
    }

    get classFromDecoration() {
        const ctx = this.props.record.evalContextWithVirtualIds;
        for (const name in this.props.decorations) {
            if (evaluateBooleanExpr(this.props.decorations[name], ctx)) {
                return `text-bg-${name}`;
            }
        }
        return "";
    }

    onCellBlur = (event, row, col) => {
        const newValue = event.target.innerText;
        event.target.innerText = newValue;
        this.state.rows[row][col] = newValue;
        // Update the record with the new value
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    addRow = () => {
        const cols = this.state.rows[0] ? this.state.rows[0].length : 0;
        this.state.rows.push(Array(cols).fill(''));
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteRow = (idx) => {
        if (idx === 0) {
            // Don't allow deleting the header row
            return;
        }
        this.state.rows.splice(idx, 1);
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    generateOrderLines = () => {
        this.props.record.model.getMethod('generate_order_lines_from_quantity_list')([this.props.record.resId]);
        this.notification.add(
            _t("Order lines generated from quantity list"),
            {
                type: 'success',
                sticky: false,
                title: _t("Success"),
            }
        );
    }

    getTotalQuantity() {
        let total = 0;
        // Skip header row (index 0)
        for (let i = 1; i < this.state.rows.length; i++) {
            const row = this.state.rows[i];
            if (row.length >= 2) {
                const qty = row[1] ? parseInt(row[1], 10) : 0;
                if (!isNaN(qty)) {
                    total += qty;
                }
            }
        }
        return total;
    }

    updateOrderQuantity = () => {
        const total = this.getTotalQuantity();
        // Update the quantity field on the order
        if (total > 0) {
            this.props.record.update({ 'quantity': total });
            this.notification.add(
                _t("Order quantity updated to %s", total),
                {
                    type: 'success',
                    sticky: false,
                    title: _t("Success"),
                }
            );
        }
    }

    saveTemplate = async () => {
        const tableData = JSON.stringify(this.state.rows);
        
        return new Promise((resolve) => {
            this.dialog.add(TemplateNameDialog, {
                confirm: async (templateName) => {
                    try {
                        const result = await this.rpc('/production_management/save_quantity_template', {
                            name: templateName,
                            table_data: tableData,
                            model: this.state.template_model,
                        });
                        
                        if (result.success) {
                            this.notification.add(
                                _t("Template '%s' saved successfully!", result.name),
                                {
                                    type: 'success',
                                    sticky: false,
                                    title: _t("Success"),
                                }
                            );
                        } else {
                            throw new Error(result.error || _t("Unknown error occurred"));
                        }
                    } catch (error) {
                        this.notification.add(
                            _t("Failed to save template: %s", error.message || error),
                            {
                                type: 'danger',
                                sticky: false,
                                title: _t("Error"),
                            }
                        );
                        console.error('Error saving template:', error);
                    }
                    resolve();
                },
            });
        });
    }

    useTemplate = async () => {
        try {
            // Fetch all templates
            const templates = await this.rpc('/production_management/get_quantity_templates', {
                model: this.state.template_model,
            });

            if (!templates || templates.length === 0) {
                this.notification.add(
                    _t("No templates found"),
                    {
                        type: 'warning',
                        sticky: false,
                        title: _t("Warning"),
                    }
                );
                return;
            }

            return new Promise((resolve) => {
                this.dialog.add(TemplateSelectionDialog, {
                    templates: templates,
                    confirm: async (selectedTemplate) => {
                        try {
                            const result = await this.rpc('/production_management/get_quantity_template', {
                                template_id: selectedTemplate.id,
                                model: this.state.template_model,
                            });

                            if (result) {
                                this.state.rows = JSON.parse(result.table_data);
                                this.props.record.update({ [this.props.name]: this.state.rows });
                                this.notification.add(
                                    _t("Template '%s' applied successfully!", result.name),
                                    {
                                        type: 'success',
                                        sticky: false,
                                        title: _t("Success"),
                                    }
                                );
                            }
                        } catch (error) {
                            this.notification.add(
                                _t("Failed to apply template: %s", error.message || error),
                                {
                                    type: 'danger',
                                    sticky: false,
                                    title: _t("Error"),
                                }
                            );
                            console.error('Error applying template:', error);
                        }
                        resolve();
                    },
                    close: () => {
                        resolve();
                    },
                });
            });
        } catch (error) {
            this.notification.add(
                _t("Failed to load templates: %s", error.message || error),
                {
                    type: 'danger',
                    sticky: false,
                    title: _t("Error"),
                }
            );
            console.error('Error loading templates:', error);
        }
    }
}

export const quantityListTableField = {
    component: QuantityListTable,
    displayName: _t("Quantity List"),
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("quantity_list_table", quantityListTableField); 