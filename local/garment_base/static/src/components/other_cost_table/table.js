/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component, useState, onWillUpdateProps, xml } from "@odoo/owl";

const formatters = registry.category("formatters");

class TemplateNameDialog extends Component {
    static template = xml`
        <Dialog title="'Save Template'" size="'sm'" onClose="() => this.props.close()" class="o_dialog_mobile">
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
                        t-on-click="() => this.props.close()">
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
        <Dialog title="'Select Template'" size="'md'" onClose="() => this.props.close()" class="o_dialog_mobile">
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
                        t-on-click="() => this.props.close()">
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

export class OtherCostTable extends Component {
    static template = "garment.OtherCostTable";
    static props = {
        ...standardFieldProps,
        decorations: { type: Object, optional: true },
        options: { type: Object, optional: true },
    };
    static defaultProps = {
        decorations: {},
        options: {},
    };

    getFormattedValue(props = this.props) {
        const fieldDef = props.record.fields[props.name];
        const rawValue = props.record.data[props.name];

        if (fieldDef.type === 'json' || fieldDef.type === 'text') {
            try {
                const parsedValue = typeof rawValue === 'string'
                    ? JSON.parse(rawValue)
                    : rawValue;
                // Ensure each row has all required fields
                return Array.isArray(parsedValue) ? parsedValue.map(row => ({
                    cost_name: row.cost_name || "",
                    amount: parseInt(row.amount) || 0,
                })) : [];
            } catch (e) {
                console.error('Invalid JSON in field', rawValue);
                return [];
            }
        }

        const formatter = formatters.get(fieldDef.type);
        return formatter(rawValue, {
            selection: fieldDef.selection,
        });
    }

    get formattedValue() {
        return this.getFormattedValue();
    }

    setup() {
        this.rpc = useService('rpc');
        this.dialog = useService("dialog");
        this.actionService = useService("action");
        this.notification = useService("notification");

        const initialValue = this.formattedValue;
        this.state = useState({
            rows: Array.isArray(initialValue) ? initialValue.slice() : [],
            template_model: 'garment.other_cost',
        });

        onWillUpdateProps((nextProps) => {
            const rawValue = nextProps.record.data[this.props.name];

            // Check if we have valid data
            if (Array.isArray(rawValue) && rawValue.length > 0) {
                const newValue = this.getFormattedValue(nextProps);
                this.state.rows.splice(0, this.state.rows.length, ...newValue);
            } else if (rawValue === null || rawValue === undefined || rawValue === false) {
                // Only clear data if the field is truly empty/null/undefined/false
                // This prevents overriding existing data when dialog is discarded
                this.state.rows.splice(0, this.state.rows.length);
            }
            // If rawValue is not a valid array but not null/undefined, keep existing data
        });
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

    updateCell = (event, field, rowIndex) => {
        const value = field === 'amount' ? parseInt(event.target.value) || 0 : event.target.value;
        this.state.rows[rowIndex][field] = value;
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    addRow = () => {
        this.state.rows.push({ cost_name: '', amount: 0 });
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteRow = (idx) => {
        this.state.rows.splice(idx, 1);
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    saveTemplate = async () => {
        const tableData = this.state.rows;

        return new Promise((resolve) => {
            this.dialog.add(TemplateNameDialog, {
                confirm: async (templateName) => {
                    try {
                        const result = await this.rpc(`/garment/save_template`, {
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
            const templates = await this.rpc(`/garment/get_templates`, {
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
                            const result = await this.rpc(`/garment/get_template`, {
                                template_id: selectedTemplate.id,
                                model: this.state.template_model,
                            });

                            if (result) {
                                console.log('Raw template data:', result.table_data);
                                let templateData;

                                if (typeof result.table_data === 'string') {
                                    // Convert Python-style string to proper JSON string
                                    const jsonStr = result.table_data
                                        .replace(/'/g, '"')  // Replace single quotes with double quotes
                                        .replace(/True/g, 'true')  // Replace Python boolean
                                        .replace(/False/g, 'false')  // Replace Python boolean
                                        .replace(/None/g, 'null');  // Replace Python None

                                    try {
                                        templateData = JSON.parse(jsonStr);
                                    } catch (e) {
                                        console.error('Failed to parse template data:', e);
                                        throw new Error('Invalid template data format');
                                    }
                                } else {
                                    templateData = result.table_data;
                                }

                                console.log('Parsed template data:', templateData);

                                // Ensure each row has all required fields
                                this.state.rows = templateData.map(row => ({
                                    cost_name: row.cost_name || "",
                                    amount: parseInt(row.amount) || 0,
                                }));

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

export const tableField = {
    component: OtherCostTable,
    displayName: _t("Table"),
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("other_cost_table", tableField);
