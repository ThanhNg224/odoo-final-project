/** @odoo-module **/

import { registry } from "@web/core/registry";

const { Component, onMounted, useState } = owl;

export class QuantityListTable extends Component {
    setup() {
        this.state = useState({
            rows: []
        });
        
        onMounted(() => {
            this.initTable();
        });
    }
    
    initTable() {
        // Find the quantityList field
        const field = this.props.record.data.quantity_list;
        let data;
        
        try {
            data = typeof field === 'string' ? JSON.parse(field) : field;
            if (!Array.isArray(data) || data.length === 0) {
                data = [["Size", "Quantity"]];
            }
        } catch (e) {
            console.error("Error parsing quantity list:", e);
            data = [["Size", "Quantity"]];
        }
        
        // Skip header row (data[0]) and populate the table
        this.state.rows = data.slice(1).map(row => ({
            size: row[0] || '',
            quantity: row[1] || ''
        }));
        
        // Add an empty row if needed
        if (this.state.rows.length === 0) {
            this.state.rows.push({ size: '', quantity: '' });
        }
    }
    
    updateField() {
        // Create the data array with header row
        const data = [["Size", "Quantity"]];
        
        // Add all rows 
        this.state.rows.forEach(row => {
            data.push([row.size, row.quantity]);
        });
        
        // Update the field
        this.props.record.update({
            quantity_list: JSON.stringify(data)
        });
    }
    
    onSizeChange(index, event) {
        this.state.rows[index].size = event.target.value;
        this.updateField();
    }
    
    onQuantityChange(index, event) {
        this.state.rows[index].quantity = event.target.value;
        this.updateField();
    }
    
    addRow() {
        this.state.rows.push({ size: '', quantity: '' });
        this.updateField();
    }
    
    removeRow(index) {
        this.state.rows.splice(index, 1);
        if (this.state.rows.length === 0) {
            this.state.rows.push({ size: '', quantity: '' });
        }
        this.updateField();
    }
}

QuantityListTable.template = 'production_management.QuantityListTable';

registry.category("views").add('quantity_list_table', QuantityListTable); 