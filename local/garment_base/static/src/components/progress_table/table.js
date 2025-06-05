/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component, useState, onWillUpdateProps, xml, onMounted } from "@odoo/owl";

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

class EditProgressDialog extends Component {
    static template = xml`
        <Dialog title="'Edit Progress'" size="'md'" onClose="() => this.props.close()" class="o_dialog_mobile">
            <div class="p-3">
                <div class="mb-3">
                    <label class="form-label">Task Name</label>
                    <input type="text" class="form-control" t-model="state.name" required="required"/>
                </div>
                <div class="mb-3">
                    <label class="form-label">Status</label>
                    <select class="form-select" t-model="state.state">
                        <option value="not_started">Not Started</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <h5>Plan</h5>
                        <div class="mb-3">
                            <label class="form-label">Start Date</label>
                            <input type="date" class="form-control" t-model="state.plan.start_date"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">End Date</label>
                            <input type="date" class="form-control" t-model="state.plan.end_date"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Quantity</label>
                            <input type="number" class="form-control" t-model="state.plan.quantity" min="0"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Person in Charge</label>
                            <input type="text" class="form-control" t-model="state.plan.person_in_charge"/>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h5>Actual</h5>
                        <div class="mb-3">
                            <label class="form-label">Start Date</label>
                            <input type="date" class="form-control" t-model="state.actual.start_date"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">End Date</label>
                            <input type="date" class="form-control" t-model="state.actual.end_date"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Total Quantity</label>
                            <input type="number" class="form-control" t-model="state.actual.total_quantity" min="0"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Completed Quantity</label>
                            <input type="number" class="form-control" t-model="state.actual.completed_quantity" min="0"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Defect Quantity</label>
                            <input type="number" class="form-control" t-model="state.actual.defect_quantity" min="0"/>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Department</label>
                            <select class="form-select" t-model="state.actual.department_id">
                                <option value="false">Select Department</option>
                                <t t-if="state.departments">
                                    <t t-foreach="state.departments" t-as="dept" t-key="dept.id">
                                        <option t-att-value="dept.id">
                                            <t t-esc="dept.name"/>
                                        </option>
                                    </t>
                                </t>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Unit Price</label>
                            <input type="number" class="form-control" t-model="state.actual.unit_price" min="0" step="0.01"/>
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Remark</label>
                    <textarea class="form-control" t-model="state.remark" rows="3"></textarea>
                </div>
            </div>
            <t t-set-slot="footer">
                <div class="text-end">
                    <button type="button" class="btn btn-secondary me-2" t-on-click="() => this.props.close()">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-primary" t-on-click="onConfirm">
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
        row: Object,
    };

    setup() {
        this.rpc = useService('rpc');
        this.state = useState({
            name: this.props.row.name || "",
            state: this.props.row.state || "not_started",
            plan: {
                start_date: this.props.row.plan?.start_date || "",
                end_date: this.props.row.plan?.end_date || "",
                quantity: this.props.row.plan?.quantity || 0,
                person_in_charge: this.props.row.plan?.person_in_charge || ""
            },
            actual: {
                start_date: this.props.row.actual?.start_date || "",
                end_date: this.props.row.actual?.end_date || "",
                total_quantity: this.props.row.actual?.total_quantity || 0,
                completed_quantity: this.props.row.actual?.completed_quantity || 0,
                defect_quantity: this.props.row.actual?.defect_quantity || 0,
                department_id: this.props.row.actual?.department_id || false,
                unit_price: this.props.row.actual?.unit_price || 0
            },
            remark: this.props.row.remark || "",
            departments: []
        });

        this.loadDepartments();
    }

    async loadDepartments() {
        try {
            // console.log("Loading departments...");
            const departments = await this.rpc('/garment/department/search_read', {
                fields: ['id', 'name'],
                domain: []
            });
            // console.log("Loaded departments:", departments);
            if (departments && departments.length > 0) {
                this.state.departments = departments;
            } else {
                console.warn("No departments found");
                this.state.departments = [];
            }
        } catch (error) {
            console.error("Error loading departments:", error);
            this.state.departments = [];
        }
    }

    onConfirm = () => {
        if (!this.state.name.trim()) {
            this.props.env.services.notification.add(_t("Task name is required"), {
                type: "warning",
            });
            return;
        }

        this.props.confirm({
            name: this.state.name.trim(),
            state: this.state.state,
            plan: {
                start_date: this.state.plan.start_date,
                end_date: this.state.plan.end_date,
                quantity: parseInt(this.state.plan.quantity) || 0,
                person_in_charge: this.state.plan.person_in_charge.trim()
            },
            actual: {
                start_date: this.state.actual.start_date,
                end_date: this.state.actual.end_date,
                total_quantity: parseInt(this.state.actual.total_quantity) || 0,
                completed_quantity: parseInt(this.state.actual.completed_quantity) || 0,
                defect_quantity: parseInt(this.state.actual.defect_quantity) || 0,
                department_id: this.state.actual.department_id,
                unit_price: parseFloat(this.state.actual.unit_price) || 0
            },
            remark: this.state.remark.trim()
        });
        this.props.close();
    }
}

class DeleteConfirmationDialog extends Component {
    static template = xml`
        <Dialog title="'Delete Progress'" size="'sm'" onClose="() => this.props.close()" class="o_dialog_mobile">
            <div class="p-3">
                <p>Are you sure you want to delete this progress item?</p>
            </div>
            <t t-set-slot="footer">
                <div class="text-end">
                    <button type="button" class="btn btn-secondary me-2" t-on-click="() => this.props.close()">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-danger" t-on-click="onConfirm">
                        Delete
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

    onConfirm = () => {
        this.props.confirm();
        this.props.close();
    }
}

export class ProgressTable extends Component {
    static template = "garment.ProgressTable";
    static components = { EditProgressDialog, TemplateSelectionDialog, DeleteConfirmationDialog };
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
            rows: Array.isArray(this.props.record.data[this.props.name]) ? this.props.record.data[this.props.name] : [],
            template_model: "garment.progress_template",
            protectedColumns: ['name', 'state', 'plan', 'actual', 'remark'],
            showTemplateDropdown: false,
            activeCell: null,
            dropdownPosition: null,
            forceUpdate: 0,
            departments: {}
        });

        onMounted(() => {
            this.initializeData();
            this.loadDepartments();
        });
    }

    async initializeData() {
        if (!this.state.rows.length) {
            this.state.rows = [];
            this.props.record.update({ [this.props.name]: this.state.rows });
        }
    }

    getStateClass(state) {
        const stateClasses = {
            'not_started': 'text-muted',
            'in_progress': 'text-blue',
            'completed': 'text-success',
        };
        return stateClasses[state] || 'text-muted';
    }

    async editRow(index) {
        const row = this.state.rows[index];
        return new Promise((resolve) => {
            this.dialog.add(EditProgressDialog, {
                row: row,
                confirm: (updatedRow) => {
                    this.state.rows[index] = updatedRow;
                    this.props.record.update({ [this.props.name]: this.state.rows });
                    this.state.forceUpdate++;
                    this.notification.add(_t("Progress updated successfully"), {
                        type: "success",
                    });
                    resolve();
                },
                close: () => resolve(),
            });
        });
    }

    async saveTemplate() {
        if (!this.state.rows.length) {
            this.notification.add(_t("No progress data to save"), {
                type: "warning",
            });
            return;
        }

        return new Promise((resolve) => {
            this.dialog.add(TemplateNameDialog, {
                confirm: async (templateName) => {
                    try {
                        const result = await this.rpc(`/garment/save_template`, {
                            name: templateName.trim(),
                            table_data: this.state.rows,
                            model: this.state.template_model
                        });

                        if (result.success) {
                            this.notification.add(_t("Template saved successfully"), {
                                type: "success",
                            });
                        } else {
                            this.notification.add(result.message || _t("Failed to save template"), {
                                type: "danger",
                            });
                        }
                    } catch (error) {
                        console.error("Error saving template:", error);
                        this.notification.add(_t("Error saving template"), {
                            type: "danger",
                        });
                    }
                    resolve();
                },
                close: () => {
                    resolve();
                },
            });
        });
    }

    async useTemplate() {
        try {
            const templates = await this.rpc(`/garment/get_templates`, {
                model: this.state.template_model
            });

            if (!templates || templates.length === 0) {
                this.notification.add(_t("No templates available"), {
                    type: "warning",
                });
                return;
            }

            return new Promise((resolve) => {
                this.dialog.add(TemplateSelectionDialog, {
                    templates: templates,
                    confirm: async (selectedTemplate) => {
                        try {
                            const templateData = await this.rpc(`/garment/get_template`, {
                                template_id: selectedTemplate.id,
                                model: this.state.template_model
                            });

                            if (templateData && templateData.table_data) {
                                this.state.rows = templateData.table_data;
                                this.props.record.update({ [this.props.name]: this.state.rows });
                                this.state.forceUpdate++;
                                this.notification.add(_t("Template loaded successfully"), {
                                    type: "success",
                                });
                            }
                        } catch (error) {
                            console.error("Error loading template:", error);
                            this.notification.add(_t("Error loading template"), {
                                type: "danger",
                            });
                        }
                        resolve();
                    },
                    close: () => resolve(),
                });
            });
        } catch (error) {
            console.error("Error loading templates:", error);
            this.notification.add(_t("Error loading templates"), {
                type: "danger",
            });
        }
    }

    updateRow(index, field, value) {
        if (field.includes('.')) {
            const [parent, child] = field.split('.');
            this.state.rows[index][parent][child] = value;
        } else {
            this.state.rows[index][field] = value;
        }

        this.props.record.update({ [this.props.name]: this.state.rows });
        this.state.forceUpdate++;
    }

    addRow() {
        this.state.rows.push({
            name: "Unnamed",
            state: "not_started",
            plan: {
                start_date: "",
                end_date: "",
                quantity: 0,
                person_in_charge: ""
            },
            actual: {
                start_date: "",
                end_date: "",
                total_quantity: 0,
                completed_quantity: 0,
                defect_quantity: 0,
                department_id: "",
                unit_price: 0
            },
            remark: ""
        });

        this.props.record.update({ [this.props.name]: this.state.rows });
        this.state.forceUpdate++;
    }

    async removeRow(index) {
        return new Promise((resolve) => {
            this.dialog.add(DeleteConfirmationDialog, {
                confirm: () => {
                    this.state.rows.splice(index, 1);
                    this.props.record.update({ [this.props.name]: this.state.rows });
                    this.state.forceUpdate++;
                    this.notification.add(_t("Progress deleted successfully"), {
                        type: "success",
                    });
                    resolve();
                },
                close: () => resolve(),
            });
        });
    }

    moveRow(index, direction) {
        const newIndex = index + direction;
        if (newIndex >= 0 && newIndex < this.state.rows.length) {
            const row = this.state.rows[index];
            this.state.rows.splice(index, 1);
            this.state.rows.splice(newIndex, 0, row);
            this.props.record.update({ [this.props.name]: this.state.rows });
            this.state.forceUpdate++;
        }
    }

    async loadDepartments() {
        try {
            // console.log("Loading departments in ProgressTable...");
            const departments = await this.rpc('/garment/department/search_read', {
                fields: ['id', 'name'],
                domain: []
            });
            // console.log("Loaded departments in ProgressTable:", departments);
            const deptMap = {};
            departments.forEach(dept => {
                deptMap[dept.id] = dept.name;
            });
            this.state.departments = deptMap;
        } catch (error) {
            console.error("Error loading departments in ProgressTable:", error);
            this.state.departments = {};
        }
    }

    get departmentNames() {
        return this.state.departments;
    }

    getDepartmentName(departmentId) {
        return this.state.departments[departmentId] || '-';
    }
}

export const progressTableField = {
    component: ProgressTable,
    displayName: "Progress Table",
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("progress_template", progressTableField);
