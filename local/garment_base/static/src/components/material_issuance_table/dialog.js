/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class MaterialIssuanceDialog extends Component {
    static template = "garment.MaterialIssuanceDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        confirm: { type: Function },
        record: { type: Object },
    };

    // Helper function to round numbers to 2 decimal places
    static roundToTwo(num) {
        return Math.round((num + Number.EPSILON) * 100) / 100;
    }

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            materials: [],
            allColors: [], // Store all colors
            availableColors: [], // Store filtered colors for selected material
            formData: {
                material_id: "",
                color_id: "",
                type: "out",
                used_quantity: 0,
                defective_quantity: 0,
                unit_price: 0,
                total_price: 0,
                receiving_company: "",
                remark: "",
            },
            get totalQuantity() {
                const usedQty = MaterialIssuanceDialog.roundToTwo(parseFloat(this.formData.used_quantity) || 0);
                const defectiveQty = MaterialIssuanceDialog.roundToTwo(parseFloat(this.formData.defective_quantity) || 0);
                return MaterialIssuanceDialog.roundToTwo(usedQty + defectiveQty);
            }
        });

        onWillStart(async () => {
            await this.loadMaterials();
        });
        // Store materialDetail for later color filtering
        this.materialDetail = [];
    }

    async loadMaterials() {
        try {
            // Get sample data including material_detail
            const recordId = parseInt(this.props.record.resId);
            // // console.log("Record ID:", recordId, "Record:", this.props.record); // Debug log
            
            const samples = await this.rpc("/garment/sample/search_read", {
                fields: ['id', 'name', 'material_detail'],
                domain: [['id', '=', recordId]] // Get only the current sample
            });
            
            if (samples && samples.length > 0) {
                let materialDetail = samples[0].material_detail;
                // // console.log("Raw material detail:", materialDetail); // Debug log
                // // console.log("Type of material detail:", typeof materialDetail); // Debug log
                // // console.log("Is Array?", Array.isArray(materialDetail)); // Debug log

                // Handle case where materialDetail might be a string
                if (typeof materialDetail === 'string') {
                    try {
                        materialDetail = JSON.parse(materialDetail);
                    } catch (e) {
                        console.error("Failed to parse materialDetail:", e);
                        materialDetail = [];
                    }
                }

                // Ensure materialDetail is an array
                if (!Array.isArray(materialDetail)) {
                    console.error("materialDetail is not an array:", materialDetail);
                    materialDetail = [];
                }

                if (materialDetail && materialDetail.length > 1) {
                    // Get header row and create column mapping
                    const headerRow = materialDetail[0];
                    const columnMap = {
                        materialName: headerRow.indexOf("Material Name"),
                        materialCode: headerRow.indexOf("Material Code"),
                        color: headerRow.indexOf("Color"),
                        colorCode: headerRow.indexOf("Color Code"),
                        specification: headerRow.indexOf("Specification"),
                        unit: headerRow.indexOf("Unit"),
                        part: headerRow.indexOf("Part"),
                        quantityPerUnit: headerRow.indexOf("Quantity per Unit"),
                        lossPerUnit: headerRow.indexOf("Loss per Unit"),
                        unitQuantity: headerRow.indexOf("Unit Quantity"),
                        totalQuantity: headerRow.indexOf("Total Quantity Used"),
                        unitPrice: headerRow.indexOf("Unit Price"),
                        supplier: headerRow.indexOf("Supplier")
                    };

                    // Use Map to store unique materials by code
                    const uniqueMaterials = new Map();
                    
                    // Skip header row and process material rows
                    materialDetail.slice(1).forEach(row => {
                        const materialCode = row[columnMap.materialCode] || ''; // Material Code
                        if (materialCode && !uniqueMaterials.has(materialCode)) {
                            uniqueMaterials.set(materialCode, {
                                code: materialCode, // Material Code
                                name: row[columnMap.materialName] || '', // Material Name
                                color: row[columnMap.color] || '', // Color
                                colorCode: row[columnMap.colorCode] || '', // Color Code
                                specification: row[columnMap.specification] || '', // Specification
                                unit: row[columnMap.unit] || '', // Unit
                                part: row[columnMap.part] || '', // Part
                                quantityPerUnit: MaterialIssuanceDialog.roundToTwo(parseFloat(row[columnMap.quantityPerUnit]) || 0), // Quantity per Unit
                                lossPerUnit: MaterialIssuanceDialog.roundToTwo(parseFloat(row[columnMap.lossPerUnit]) || 0), // Loss per Unit
                                unitQuantity: MaterialIssuanceDialog.roundToTwo(parseFloat(row[columnMap.unitQuantity]) || 0), // Unit Quantity
                                totalQuantity: MaterialIssuanceDialog.roundToTwo(parseFloat(row[columnMap.totalQuantity]) || 0), // Total Quantity Used
                                unit_price: MaterialIssuanceDialog.roundToTwo(parseFloat(row[columnMap.unitPrice]) || 0), // Unit Price
                                supplier: row[columnMap.supplier] || '', // Supplier
                                material_id: null // Will be set after materials are loaded from backend
                            });
                        }
                    });
                    
                    // Convert Map values back to array
                    this.state.materials = Array.from(uniqueMaterials.values());
                }

                this.materialDetail = materialDetail; // Store for later use
            } else {
                this.materialDetail = [];
            }

            // Get colors for the dropdown
            const colors = await this.rpc("/garment/get_colors");
            this.state.allColors = colors;
            this.state.availableColors = colors; // Initially show all colors

            // Get all materials from backend to match codes with IDs
            const backendMaterials = await this.rpc("/garment/get_materials");
            
            // Update material_id for materials after backend materials are loaded
            if (this.state.materials.length > 0) {
                this.state.materials = this.state.materials.map(material => {
                    const backendMaterial = backendMaterials.find(m => m.code === material.code);
                    return {
                        ...material,
                        material_id: backendMaterial ? backendMaterial.id : null
                    };
                });

                // Filter out materials that don't exist in backend
                this.state.materials = this.state.materials.filter(m => m.material_id !== null);
            }

            // console.log("Final materials:", this.state.materials); // Debug log
        } catch (error) {
            console.error("Error loading materials:", error);
            this.notification.add(_t("Failed to load materials. Please try again."), {
                type: "danger",
                sticky: true,
            });
        }
    }

    onMaterialChange(event) {
        const materialId = parseInt(event.target.value);
        this.state.formData.material_id = materialId;
        this.state.formData.color_id = "";
        this.state.formData.used_quantity = 0;
        this.state.formData.defective_quantity = 0;
        this.state.formData.unit_price = 0;
        this.state.formData.total_price = 0;
        
        // Update available colors based on selected material
        if (materialId) {
            const selectedMaterial = this.state.materials.find(m => m.material_id === materialId);
            if (selectedMaterial) {
                // Get header row and create column mapping
                const headerRow = this.materialDetail[0];
                const columnMap = {
                    materialCode: headerRow.indexOf("Material Code"),
                    colorCode: headerRow.indexOf("Color Code")
                };

                // Filter colors based on material code
                const relatedRows = this.materialDetail
                    .filter(row => row[columnMap.materialCode] === selectedMaterial.code);
                // Get unique color codes from those rows
                const uniqueColorCodes = [...new Set(relatedRows.map(row => row[columnMap.colorCode]))];
                this.state.availableColors = this.state.allColors.filter(color => 
                    uniqueColorCodes.includes(color.code)
                );
            }
        } else {
            this.state.availableColors = this.state.allColors; // Reset to all colors if no material selected
        }
    }

    onColorChange(event) {
        const colorId = parseInt(event.target.value);
        this.state.formData.color_id = colorId;

        // Find the corresponding row in materialDetail for the selected material and color
        if (this.state.formData.material_id && colorId) {
            const selectedMaterial = this.state.materials.find(m => m.material_id === this.state.formData.material_id);
            const selectedColor = this.state.allColors.find(c => c.id === colorId);
            
            if (selectedMaterial && selectedColor) {
                // Get header row and create column mapping
                const headerRow = this.materialDetail[0];
                const columnMap = {
                    materialCode: headerRow.indexOf("Material Code"),
                    colorCode: headerRow.indexOf("Color Code"),
                    quantityPerUnit: headerRow.indexOf("Quantity per Unit"),
                    lossPerUnit: headerRow.indexOf("Loss per Unit"),
                    unitQuantity: headerRow.indexOf("Unit Quantity"),
                    unitPrice: headerRow.indexOf("Unit Price")
                };

                // Find the matching row in materialDetail
                const matchingRow = this.materialDetail.find(row => 
                    row[columnMap.materialCode] === selectedMaterial.code && // Material Code
                    row[columnMap.colorCode] === selectedColor.code // Color Code
                );

                if (matchingRow) {
                    // console.log('Found matching row:', matchingRow);
                    // Populate the form with values from the matching row
                    const quantityPerUnit = MaterialIssuanceDialog.roundToTwo(parseFloat(matchingRow[columnMap.quantityPerUnit]) || 0);
                    const unitQuantity = MaterialIssuanceDialog.roundToTwo(parseFloat(matchingRow[columnMap.unitQuantity]) || 0);
                    const lossPerUnit = MaterialIssuanceDialog.roundToTwo(parseFloat(matchingRow[columnMap.lossPerUnit]) || 0);
                    
                    // console.log('Calculated values:', {
                    //     quantityPerUnit,
                    //     unitQuantity,
                    //     lossPerUnit,
                    //     unitPrice: matchingRow[columnMap.unitPrice]
                    // });

                    this.state.formData.used_quantity = MaterialIssuanceDialog.roundToTwo(quantityPerUnit * unitQuantity); // Used Quantity
                    this.state.formData.defective_quantity = MaterialIssuanceDialog.roundToTwo(lossPerUnit * unitQuantity); // Defective Quantity
                    this.state.formData.unit_price = MaterialIssuanceDialog.roundToTwo(parseFloat(matchingRow[columnMap.unitPrice]) || 0); // Unit Price
                    
                    // console.log('Updated form data:', this.state.formData);
                    this.calculateTotalPrice();
                }
            }
        }
    }

    onQuantityChange() {
        this.calculateTotalPrice();
    }

    calculateTotalPrice() {
        const usedQty = MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.used_quantity) || 0);
        const defectiveQty = MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.defective_quantity) || 0);
        const unitPrice = MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.unit_price) || 0);
        // console.log('Calculating total price with:', {
        //     usedQty,
        //     defectiveQty,
        //     unitPrice,
        //     formData: this.state.formData
        // });
        this.state.formData.total_price = MaterialIssuanceDialog.roundToTwo((usedQty + defectiveQty) * unitPrice);
        // console.log('Calculated total price:', this.state.formData.total_price);
    }

    onConfirm() {
        // Validate required fields
        if (!this.state.formData.material_id) {
            this.notification.add(_t("Please select a material"), {
                type: "warning",
            });
            return;
        }

        if (!this.state.formData.color_id) {
            this.notification.add(_t("Please select a color"), {
                type: "warning",
            });
            return;
        }

        const usedQuantity = MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.used_quantity) || 0);
        if (usedQuantity <= 0) {
            this.notification.add(_t("Used quantity must be greater than 0"), {
                type: "warning",
            });
            return;
        }

        // Ensure proper data types
        const formData = {
            ...this.state.formData,
            material_id: parseInt(this.state.formData.material_id),
            color_id: parseInt(this.state.formData.color_id),
            used_quantity: MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.used_quantity) || 0),
            defective_quantity: MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.defective_quantity) || 0),
            unit_price: MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.unit_price) || 0),
            total_price: MaterialIssuanceDialog.roundToTwo(parseFloat(this.state.formData.total_price) || 0),
            item_type: 'material', // Set item_type to 'material'
            type: 'out' // Ensure type is 'out' for material issuance
        };

        // Log the data being sent
        // console.log("Sending material issuance data:", formData);

        try {
            this.props.confirm(formData);
            this.props.close();
        } catch (error) {
            console.error("Error in onConfirm:", error);
            this.notification.add(_t("Failed to create material issuance record. Please try again."), {
                type: "danger",
                sticky: true,
            });
        }
    }
}
