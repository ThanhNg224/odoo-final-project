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

export class SpecificationDetailTable extends Component {
    static template = "garment.SpecificationDetailTable";
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
            rows: Array.isArray(this.formattedValue) ? this.formattedValue : [
                ["Color", "XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL"],
                ['', 0, 0, 0, 0, 0, 0, 0, 0],
            ],
            template_model: "garment.specification_detail",
            availableSizes: ["XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"],
            existingSizes: [],
        });

        // Initialize existing sizes
        this.updateExistingSizes();

        onWillUpdateProps((nextProps) => {
            const rawValue = nextProps.record.data[this.props.name];
            let newArray;

            // Check if we have valid data
            if (Array.isArray(rawValue) && rawValue.length > 0) {
                newArray = rawValue;
            } else if (rawValue === null || rawValue === undefined || rawValue === false) {
                // Only use default values if the field is truly empty/null/undefined/false
                // This prevents overriding existing data when dialog is discarded
                newArray = [
                    ["Color", "XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL"],
                    ['', 0, 0, 0, 0, 0, 0, 0, 0],
                ];
            } else {
                // Keep existing data if the new value is not a valid array but not null/undefined
                return;
            }

            this.state.rows.splice(0, this.state.rows.length, ...newArray);
            this.updateExistingSizes();
        });
    }

    // Update the list of existing sizes in the table
    updateExistingSizes = () => {
        if (this.state.rows.length > 0) {
            // Skip the "Color" column (index 0)
            this.state.existingSizes = this.state.rows[0].slice(1);
        } else {
            this.state.existingSizes = [];
        }
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
                return [];
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

    toggleSizeColumn = (size) => {
        const index = this.state.rows[0].indexOf(size);
        if (index > 0) {
            this.deleteColumn(index);
        } else {
            this.addSizeColumn(size);
        }
    };

    addSizeColumn = (size) => {
        if (this.state.existingSizes.includes(size)) {
            return;
        }

        // Find the correct insertion position based on availableSizes order
        const sizeOrderIndex = this.state.availableSizes.indexOf(size);
        if (sizeOrderIndex === -1) {
            // If size is not in availableSizes, add it to the end
            this.state.rows[0].push(size);
            for (let i = 1; i < this.state.rows.length; i++) {
                this.state.rows[i].push(0);
            }
        } else {
            // Find the correct position to insert the column
            let insertPosition = this.state.rows[0].length; // Default to end

            // Look for the position where this size should be inserted
            for (let i = 1; i < this.state.rows[0].length; i++) { // Start from 1 to skip "Color" column
                const currentSize = this.state.rows[0][i];
                const currentSizeOrderIndex = this.state.availableSizes.indexOf(currentSize);

                // If current size comes after the new size in the order, insert before it
                if (currentSizeOrderIndex > sizeOrderIndex || currentSizeOrderIndex === -1) {
                    insertPosition = i;
                    break;
                }
            }

            // Insert the new size column at the correct position in all rows
            for (let i = 0; i < this.state.rows.length; i++) {
                if (i === 0) {
                    // Insert size name in header row
                    this.state.rows[i].splice(insertPosition, 0, size);
                } else {
                    // Insert 0 value in data rows
                    this.state.rows[i].splice(insertPosition, 0, 0);
                }
            }
        }

        this.props.record.update({ [this.props.name]: this.state.rows });
        this.updateExistingSizes();
    }

    onCellBlur = (event, row, col) => {
        const newValue = event.target.innerText;
        event.target.innerText = newValue;

        // Convert to number for size columns (all columns except first)
        if (col > 0) {
            this.state.rows[row][col] = parseFloat(newValue) || 0;
        } else {
            this.state.rows[row][col] = newValue;
        }

        // Update the record with the new value
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    addRow = () => {
        const cols = this.state.rows[0] ? this.state.rows[0].length : 0;
        const newRow = Array(cols).fill('');
        // Set first column (Color) to empty string, others to 0
        for (let i = 1; i < cols; i++) {
            newRow[i] = 0;
        }
        this.state.rows.push(newRow);
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteRow = (idx) => {
        // Prevent deleting first two rows
        if (idx <= 1) return;
        this.state.rows.splice(idx, 1);
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteColumn = (colIndex) => {
        if (colIndex === 0) return;
        this.state.rows.forEach(row => row.splice(colIndex, 1));
        this.props.record.update({ [this.props.name]: this.state.rows });
        this.updateExistingSizes(); // Update existing sizes after deletion
    }

    getRowSum = (row) => {
        return row
            .slice(1)
            .reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
    };

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
            // Fetch all templates
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
                                this.state.rows = JSON.parse(result.table_data);
                                this.props.record.update({ [this.props.name]: this.state.rows });
                                this.updateExistingSizes(); // Update existing sizes after applying template
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
    component: SpecificationDetailTable,
    displayName: _t("Specification Detail Table"),
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("specification_detail_table", tableField);
