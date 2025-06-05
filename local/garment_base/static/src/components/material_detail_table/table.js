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

export class MaterialDetailTable extends Component {
    static template = "garment.MaterialDetailTable";
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
                ['Material Name', 'Material Code', 'Color', 'Color Code', 'Specification', 'Unit', 'Part', 'Quantity per Unit', 'Loss per Unit', 'Unit Quantity', 'Total Quantity Used', 'Unit Price', 'Supplier'],
                ['', '', '', '', '', '', '', 0, 0, 0, 0, 0, '']
            ],
            template_model: "garment.material_detail",
            protectedColumns: ['Material Name', 'Material Code', 'Color', 'Color Code', 'Specification', 'Unit', 'Part', 'Quantity per Unit', 'Loss per Unit', 'Unit Quantity', 'Total Quantity Used', 'Unit Price', 'Supplier'],
            originalColumnCount: 10,
            materials: [],
            colors: [],
            showMaterialDropdown: false,
            showColorDropdown: false,
            activeCell: null,
            dropdownPosition: null,
            forceUpdate: 0
        });

        // Initialize calculations for all rows
        this.initializeCalculations();

        // Fetch materials and colors on component setup
        this.fetchMaterials();
        this.fetchColors();

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
                    ['Material Name', 'Material Code', 'Color', 'Color Code', 'Specification', 'Unit', 'Part', 'Quantity per Unit', 'Loss per Unit', 'Unit Quantity', 'Total Quantity Used', 'Unit Price', 'Supplier'],
                    ['', '', '', '', '', '', '', 0, 0, 0, 0, 0, '']
                ];
            } else {
                // Keep existing data if the new value is not a valid array but not null/undefined
                return;
            }

            this.state.rows.splice(0, this.state.rows.length, ...newArray);

            // Re-initialize calculations when data is updated
            this.initializeCalculations();
        });
    }

    initializeCalculations() {
        // Skip the header row (index 0)
        for (let i = 1; i < this.state.rows.length; i++) {
            this.calculateTotalQuantity(i);
        }
    }

    // Fetch materials from the server
    async fetchMaterials() {
        try {
            const materials = await this.rpc(`/garment/get_materials`, {});
            this.state.materials = materials;
        } catch (error) {
            console.error('Error fetching materials:', error);
            this.notification.add(
                _t("Failed to load materials"),
                {
                    type: 'danger',
                    sticky: false,
                    title: _t("Error"),
                }
            );
        }
    }

    // Fetch colors from the server
    async fetchColors() {
        try {
            const colors = await this.rpc(`/garment/get_colors`, {});
            this.state.colors = colors;
        } catch (error) {
            console.error('Error fetching colors:', error);
            this.notification.add(
                _t("Failed to load colors"),
                {
                    type: 'danger',
                    sticky: false,
                    title: _t("Error"),
                }
            );
        }
    }

    // Handle cell click for material code and color code columns
    onCellClick = (event, row, col) => {
        if (row === 0 || this.props.readonly) return; // Don't handle header row or readonly mode

        const header = this.state.rows[0][col];
        if (header === 'Material Code' || header === 'Color Code') {
            const cell = event.target;
            const rect = cell.getBoundingClientRect();

            // Calculate position relative to the viewport
            const top = rect.bottom;
            const left = rect.left;

            if (header === 'Material Code') {
                this.state.showMaterialDropdown = true;
                this.state.showColorDropdown = false;
            } else {
                this.state.showMaterialDropdown = false;
                this.state.showColorDropdown = true;
            }

            this.state.activeCell = { row, col };
            this.state.dropdownPosition = {
                top: top,
                left: left
            };
        } else {
            this.state.showMaterialDropdown = false;
            this.state.showColorDropdown = false;
            this.state.activeCell = null;
            this.state.dropdownPosition = null;
        }
    }

    // Handle material selection
    onMaterialSelect = (material) => {
        if (this.state.activeCell) {
            const { row, col } = this.state.activeCell;

            // Find the material name column index
            const materialNameCol = this.state.rows[0].indexOf('Material Name');

            // console.log('Before update - Current cell value:', this.state.rows[row][col]);
            // console.log('Before update - Material name cell value:', this.state.rows[row][materialNameCol]);

            // Create a new row array to ensure reactivity
            const updatedRow = [...this.state.rows[row]];
            updatedRow[col] = material.code;
            updatedRow[materialNameCol] = material.name;

            // Update the entire row
            this.state.rows[row] = updatedRow;

            // console.log('After update - Current cell value:', this.state.rows[row][col]);
            // console.log('After update - Material name cell value:', this.state.rows[row][materialNameCol]);

            // Force a UI update
            this.state.forceUpdate++;

            // Update the record with a new array
            this.props.record.update({ [this.props.name]: [...this.state.rows] });

            // Hide dropdown
            this.state.showMaterialDropdown = false;
            this.state.activeCell = null;
            this.state.dropdownPosition = null;

        }
    }

    // Handle color selection
    onColorSelect = (color) => {
        if (this.state.activeCell) {
            const { row, col } = this.state.activeCell;

            // Find the color name column index
            const colorNameCol = this.state.rows[0].indexOf('Color');

            // Update color code in the clicked cell
            this.state.rows[row][col] = color.code;
            // Update color name
            this.state.rows[row][colorNameCol] = color.name;

            // Force update the record
            this.props.record.update({ [this.props.name]: [...this.state.rows] });

            // Hide dropdown
            this.state.showColorDropdown = false;
            this.state.activeCell = null;
            this.state.dropdownPosition = null;
        }
    }

    onCellBlur = (event, row, col) => {
        // Allow editing header row (row 0) only for new columns
        if (row === 0) {
            if (col < this.state.originalColumnCount) {
                // Revert changes for original columns
                event.target.innerText = this.state.rows[row][col];
                return;
            }
        }

        const header = this.state.rows[0][col];
        // Don't allow editing material name, color name, material code, color code columns and total quantity used
        if (header === 'Material Name' || header === 'Color' || header === 'Material Code' || header === 'Color Code' || header === 'Total Quantity Used') {
            event.target.innerText = this.state.rows[row][col];
            return;
        }

        const newValue = event.target.innerText;
        event.target.innerText = newValue;
        this.state.rows[row][col] = newValue;

        // Auto calculate Total Quantity Used when Quantity per Unit, Loss per Unit, or Quantity changes
        if (header === 'Quantity per Unit' || header === 'Loss per Unit' || header === 'Unit Quantity') {
            this.calculateTotalQuantity(row);
        }

        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    calculateTotalQuantity = (rowIndex) => {
        // Find the column indices
        const quantityPerItemCol = this.state.rows[0].indexOf('Quantity per Unit');
        const lossPerItemCol = this.state.rows[0].indexOf('Loss per Unit');
        const quantityCol = this.state.rows[0].indexOf('Unit Quantity');
        const totalQuantityCol = this.state.rows[0].indexOf('Total Quantity Used');

        // Make sure all necessary columns exist
        if (quantityPerItemCol !== -1 && lossPerItemCol !== -1 && quantityCol !== -1 && totalQuantityCol !== -1) {
            // Parse the values, defaulting to 0 if they're not valid numbers
            const quantityPerItem = parseFloat(this.state.rows[rowIndex][quantityPerItemCol]) || 0;
            const lossPerItem = parseFloat(this.state.rows[rowIndex][lossPerItemCol]) || 0;
            const quantity = parseFloat(this.state.rows[rowIndex][quantityCol]) || 0;

            // Calculate total quantity used
            const totalQuantity = (quantityPerItem + lossPerItem) * quantity;

            // Update the Total Quantity Used column
            this.state.rows[rowIndex][totalQuantityCol] = totalQuantity;
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

    addRow = () => {
        const cols = this.state.rows[0] ? this.state.rows[0].length : 0;
        // Create new row with empty strings and default 0 for numeric columns
        const newRow = Array(cols).fill('');

        // Find the indices of numeric columns to initialize with 0
        if (this.state.rows[0]) {
            const qtyPerItemIdx = this.state.rows[0].indexOf('Quantity per Unit');
            const lossPerItemIdx = this.state.rows[0].indexOf('Loss per Unit');
            const quantityIdx = this.state.rows[0].indexOf('Unit Quantity');
            const totalQtyIdx = this.state.rows[0].indexOf('Total Quantity Used');
            const unitPriceIdx = this.state.rows[0].indexOf('Unit Price');

            // Initialize numeric fields with 0
            if (qtyPerItemIdx !== -1) newRow[qtyPerItemIdx] = 0;
            if (lossPerItemIdx !== -1) newRow[lossPerItemIdx] = 0;
            if (quantityIdx !== -1) newRow[quantityIdx] = 0;
            if (totalQtyIdx !== -1) newRow[totalQtyIdx] = 0;
            if (unitPriceIdx !== -1) newRow[unitPriceIdx] = 0;
        }

        this.state.rows.push(newRow);

        // Calculate total quantity for the new row
        this.calculateTotalQuantity(this.state.rows.length - 1);

        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteRow = (idx) => {
        if (idx === 0) return; // Prevent deleting header row
        this.state.rows.splice(idx, 1);
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    addColumn = () => {
        this.state.rows.forEach(row => row.push(''));
        this.props.record.update({ [this.props.name]: this.state.rows });
    }

    deleteColumn = (colIndex) => {
        // Check if the column to be deleted is a protected column
        if (this.state.rows[0] && this.state.protectedColumns.includes(this.state.rows[0][colIndex])) {
            this.notification.add(
                _t("Cannot delete protected columns"),
                {
                    type: 'warning',
                    sticky: false,
                    title: _t("Warning"),
                }
            );
            return;
        }
        this.state.rows.forEach(row => row.splice(colIndex, 1));
        this.props.record.update({ [this.props.name]: this.state.rows });
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
                                let templateData;
                                try {
                                    templateData = typeof result.table_data === 'string'
                                        ? JSON.parse(result.table_data)
                                        : result.table_data;
                                } catch (e) {
                                    console.error('Error parsing template data:', e);
                                    this.notification.add(
                                        _t("Invalid template data format"),
                                        {
                                            type: 'danger',
                                            sticky: false,
                                            title: _t("Error"),
                                        }
                                    );
                                    return;
                                }

                                this.state.rows = templateData;
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
}

export const materialDetailTableField = {
    component: MaterialDetailTable,
    displayName: _t("Material Detail Table"),
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("material_detail_table", materialDetailTableField);
