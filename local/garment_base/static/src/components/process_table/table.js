/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

import { Component, useState, onWillUpdateProps, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
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

export class ProcessTable extends Component {
    static template = "garment.ProcessTable";
    static props = {
        ...standardFieldProps,
        decorations: { type: Object, optional: true },
        options: { type: Object, optional: true },
        hide_fields: { type: Array, optional: true },
    };
    static defaultProps = {
        decorations: {},
        options: {},
        hide_fields: [],
    };

    setup() {
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        const initialValue = this.formattedValue;
        this.state = useState({
            rows: Array.isArray(initialValue) ? initialValue.slice() : [],
            template_model: "garment.process_table",
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

    getFormattedValue(props = this.props) {
        const fieldDef = props.record.fields[props.name];
        const rawValue = props.record.data[props.name];

        if (fieldDef.type === 'json' || fieldDef.type === 'text') {
            try {
                const parsedValue = typeof rawValue === 'string'
                    ? JSON.parse(rawValue)
                    : rawValue;
                // Ensure each row has all required fields
                return Array.isArray(parsedValue) ? parsedValue.map((row, index) => ({
                    serial_number: row.serial_number || index + 1,
                    name: row.name || "",
                    unit_price: row.unit_price || 0,
                    multiplier: row.multiplier || 1,
                    note: row.note || "",
                    operate: row.operate || "",
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

    addRow = () => {
        const newSerialNumber = this.state.rows.length + 1;
        this.state.rows.push({
            serial_number: newSerialNumber,
            name: "",
            unit_price: 0,
            multiplier: 1,
            note: "",
            operate: "",
        });
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    removeRow = (serial_number) => {
        this.state.rows = this.state.rows.filter(r => r.serial_number !== serial_number);
        // Update serial numbers
        this.state.rows.forEach((row, index) => {
            row.serial_number = index + 1;
        });
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    updateCell = (event, field, serialNumber) => {
        const newValue = event.target.value;
        const idx = this.state.rows.findIndex(r => r.serial_number === serialNumber);
        if (idx === -1) return;

        // Convert numeric fields
        if (field === 'unit_price' || field === 'multiplier') {
            this.state.rows[idx][field] = parseFloat(newValue) || 0;
        } else {
            this.state.rows[idx][field] = newValue;
        }
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    moveUp = (serialNumber) => {
        const idx = this.state.rows.findIndex(r => r.serial_number === serialNumber);
        if (idx <= 0) return;

        // Swap rows
        [this.state.rows[idx], this.state.rows[idx - 1]] = [this.state.rows[idx - 1], this.state.rows[idx]];
        // Update serial numbers
        this.state.rows.forEach((row, index) => {
            row.serial_number = index + 1;
        });
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    moveDown = (serialNumber) => {
        const idx = this.state.rows.findIndex(r => r.serial_number === serialNumber);
        if (idx === -1 || idx >= this.state.rows.length - 1) return;

        // Swap rows
        [this.state.rows[idx], this.state.rows[idx + 1]] = [this.state.rows[idx + 1], this.state.rows[idx]];
        // Update serial numbers
        this.state.rows.forEach((row, index) => {
            row.serial_number = index + 1;
        });
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    saveTemplate = async () => {
        const tableData = JSON.stringify(this.state.rows);

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
                                const templateData = typeof result.table_data === 'string'
                                    ? JSON.parse(result.table_data)
                                    : result.table_data;

                                // Ensure each row has all required fields
                                this.state.rows = templateData.map((row, index) => ({
                                    serial_number: row.serial_number || index + 1,
                                    name: row.name || "",
                                    unit_price: row.unit_price || 0,
                                    multiplier: row.multiplier || 1,
                                    note: row.note || "",
                                    operate: row.operate || "",
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

    get classFromDecoration() {
        const evalContext = this.props.record.evalContextWithVirtualIds;
        for (const decorationName in this.props.decorations) {
            if (evaluateBooleanExpr(this.props.decorations[decorationName], evalContext)) {
                return `text-bg-${decorationName}`;
            }
        }
        return "";
    }
}

export const tableProcessField = {
    component: ProcessTable,
    displayName: _t("TableProcess"),
    supportedTypes: ["json"],
    extractProps: ({ decorations, options, attrs }) => ({
        decorations,
        options,
        hide_fields: attrs.hide_fields || [],
    }),
};

registry.category("fields").add("process_table", tableProcessField);

