/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps, xml, onMounted } from "@odoo/owl";

const formatters = registry.category("formatters");

export class ProgressDropDown extends Component {
    static template = "garment.ProgressDropdown";
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
        this.notification = useService("notification");

        this.state = useState({
            rows: Array.isArray(this.props.record.data[this.props.name]) ? this.props.record.data[this.props.name] : [],
            template_model: "garment.progress_template",
            protectedColumns: ['name', 'state', 'plan', 'actual', 'remark'],
            showTemplateDropdown: false,
            activeCell: null,
            dropdownPosition: null,
            forceUpdate: 0,
            sampleNames: {},
            selectedSampleId: ""
        });

        onMounted(() => {
            console.log("ProgressDropDown component mounted");
            this.initializeData();
            this.loadApprovedSamples();
        });

        onWillUpdateProps((nextProps) => {
            const rawValue = nextProps.record.data[this.props.name];
            let newArray;

            // Check if we have valid data
            if (Array.isArray(rawValue) && rawValue.length > 0) {
                newArray = rawValue;
            } else if (rawValue === null || rawValue === undefined || rawValue === false) {
                // Only use default values if the field is truly empty/null/undefined/false
                // This prevents overriding existing data when dialog is discarded
                newArray = [['', ''], ['', '']];
            } else {
                // Keep existing data if the new value is not a valid array but not null/undefined
                return;
            }

            this.state.rows.splice(0, this.state.rows.length, ...newArray);
        });
    }

    handleSampleSelection() {
        console.log("Sample selection changed:", this.state.selectedSampleId);
        if (this.state.selectedSampleId) {
            this.loadSampleProgress(this.state.selectedSampleId);
        }
    }

    async initializeData() {
        if (!this.state.rows.length) {
            this.state.rows = [];
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

    async loadSampleProgress(sampleId) {
        try {
            const result = await this.rpc('/garment/sample/search_read', {
                domain: [['id', '=', parseInt(sampleId)]],
                fields: ['progress_detail', 'name']
            });
            
            if (result && result.length > 0 && result[0].progress_detail) {
                const sourceSampleName = result[0].name;
                const progressDetail = result[0].progress_detail;
                
                // Create a deep copy of the progress detail
                const copiedProgress = JSON.parse(JSON.stringify(progressDetail));
                
                // Update the current sample's progress
                this.state.rows = copiedProgress;
                this.props.record.update({ [this.props.name]: this.state.rows });
            } else {
                this.notification.add(_t("No progress detail found in the selected sample"), {
                    type: "warning",
                });
                this.state.selectedSampleId = "";
            }
        } catch (error) {
            console.error("Error loading sample progress:", error);
            this.notification.add(_t("Error loading sample progress"), {
                type: "danger",
            });
            this.state.selectedSampleId = "";
        }
    }

    async loadApprovedSamples() {
        try {
            const samples = await this.rpc('/garment/sample/search_read', {
                fields: ['id', 'name'],
                domain: [
                    ['state', '=', 'in_progress'],
                    ['id', '!=', this.props.record.resId] // Exclude current sample
                ]
            });
            const sampleMap = {};
            samples.forEach(sample => {
                sampleMap[sample.id] = sample.name;
            });
            this.state.sampleNames = sampleMap;
        } catch (error) {
            console.error("Error loading approved samples in ProgressDropDown:", error);
            this.state.sampleNames = {};
        }
    }
}

export const progressTableField = {
    component: ProgressDropDown,
    displayName: "Progress Table",
    supportedTypes: ["json"],
    extractProps: ({ decorations, options }) => ({ decorations, options }),
};

registry.category("fields").add("progress_dropdown", progressTableField);