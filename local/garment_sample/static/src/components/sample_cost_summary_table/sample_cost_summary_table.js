/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { useService } from "@web/core/utils/hooks";

class SampleCostSummaryTable extends Component {
    static template = "garment_sample.SampleCostSummaryTable";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        this.rpc = useService('rpc');
        this.state = useState({
            materialCostBudget: 0,
            materialCostActual: 0,
            processCostBudget: 0,
            processCostActual: 0,
            otherCostBudget: 0,
            otherCostActual: 0,
            totalCostBudget: 0,
            totalCostActual: 0,
            quoteBudget: 0,
            quoteActual: 0,
            profitBudget: 0,
            profitActual: 0,
        });

        onMounted(() => this.fetchCostSummary());
    }

    async fetchCostSummary() {
        const sampleId = this.props.record.resId;
        if (sampleId) {
            try {
                const data = await this.rpc('/garment/sample/get_sample_cost_summary', {
                    sample_id: sampleId
                });
                if (data) {
                    // Update state with the fetched data
                    this.state.materialCostBudget = data.material_cost;
                    this.state.materialCostActual = 0;
                    this.state.processCostBudget = data.process_cost;
                    this.state.processCostActual = 0;
                    this.state.otherCostBudget = data.other_cost;
                    this.state.otherCostActual = 0;
                    this.state.quoteBudget = data.quotation;
                    this.state.quoteActual = 0;

                    // Calculate totals
                    this.state.totalCostBudget = this.state.materialCostBudget + this.state.processCostBudget + this.state.otherCostBudget;
                    this.state.totalCostActual = this.state.materialCostActual + this.state.processCostActual + this.state.otherCostActual;

                    // Calculate profits
                    this.state.profitBudget = this.state.quoteBudget - this.state.totalCostBudget;
                    this.state.profitActual = this.state.quoteActual - this.state.totalCostActual;
                }
            } catch (error) {
                console.error('Error fetching cost summary:', error);
            }
        }
    }
}

export const sampleCostSummaryTable = {
    component: SampleCostSummaryTable,
    supportedTypes: ["char", "text", "html"],
};

registry.category("view_widgets").add("sample_cost_summary_table", sampleCostSummaryTable);
