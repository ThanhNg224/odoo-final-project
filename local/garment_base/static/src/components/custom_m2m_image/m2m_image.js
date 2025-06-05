/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileInput } from "@web/core/file_input/file_input";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";
import { Component } from "@odoo/owl";

export class Many2ManyImage extends Component {
    static template = "garment.Many2ManyImage";
    static components = {
        FileInput,
    };
    static props = {
        ...standardFieldProps,
        className: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.operations = useX2ManyCrud(() => this.props.record.data[this.props.name], true);
    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    getDropzoneText() {
        return _t("Drag & Drop\nor click to upload");
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((record) => {
            return {
                ...record.data,
                id: record.resId,
            };
        });
    }

    getUrl(id) {
        return "/web/content/" + id + "?download=true";
    }

    isValidImage(file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        // For uploaded files, check file.type, for existing records check mimetype
        const fileType = file.type || file.mimetype;
        console.log('File type:', fileType, 'File:', file);
        
        // Additional check for file extension
        if (file.name) {
            const extension = file.name.split('.').pop().toLowerCase();
            const validExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
            if (!validExtensions.includes(extension)) {
                return false;
            }
        }
        
        return validTypes.includes(fileType);
    }

    onDragOver(ev) {
        ev.currentTarget.classList.add('o_dropzone_dragover');
    }

    onDragLeave(ev) {
        ev.currentTarget.classList.remove('o_dropzone_dragover');
    }

    async onDrop(ev) {
        ev.currentTarget.classList.remove('o_dropzone_dragover');
        const files = Array.from(ev.dataTransfer.files);
        const validFiles = files.filter(file => this.isValidImage(file));
        
        if (validFiles.length !== files.length) {
            this.notification.add(_t("Some files were skipped. Only image files (JPEG, JPG, PNG, GIF, WEBP) are allowed."), {
                title: _t("Invalid file type"),
                type: "warning",
            });
        }

        if (validFiles.length > 0) {
            const fileInput = ev.currentTarget.querySelector('input[type="file"]');
            if (fileInput) {
                const dataTransfer = new DataTransfer();
                validFiles.forEach(file => dataTransfer.items.add(file));
                fileInput.files = dataTransfer.files;
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }

    async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: _t("Uploading error"),
                    type: "danger",
                });
            }
            
            // Check file type before saving
            if (!file.mimetype || !file.mimetype.startsWith('image/')) {
                return this.notification.add(_t("Only image files are allowed."), {
                    title: _t("Invalid file type"),
                    type: "danger",
                });
            }
            
            // For new uploads, we need to check the actual file type
            if (file.file && !this.isValidImage(file.file)) {
                return this.notification.add(_t("Only image files (JPEG, JPG, PNG, GIF, WEBP) are allowed."), {
                    title: _t("Invalid file type"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
        }
    }

    async onFileRemove(deleteId) {
        const record = this.props.record.data[this.props.name].records.find(
            (record) => record.resId === deleteId
        );
        this.operations.removeRecord(record);
    }
}

export const many2ManyImageField = {
    component: Many2ManyImage,
    supportedTypes: ["many2many"],
    isEmpty: () => false,
    relatedFields: [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
    ],
    extractProps: ({ attrs }) => ({
        className: attrs.class,
    }),
};

registry.category("fields").add("many2many_image", many2ManyImageField);
