/** @odoo-module **/
import { ListController } from '@web/views/list/list_controller';
import { listView } from '@web/views/list/list_view';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { ListRenderer } from "@web/views/list/list_renderer";
import { _t } from "@web/core/l10n/translation";
import { useState, onMounted } from "@odoo/owl";

class CustomListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService('action');
        this.userService = useService('user');
        this.state = useState({
            canCreate: false
        });
        onMounted(() => this.checkCreatePermission());
    }

    async checkCreatePermission() {
        const userGroups = await this.userService.hasGroup('garment_authorization.group_sample_management');
        this.state.canCreate = userGroups;
    }

    onCreateButtonClick = () => {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Create Garment Sample',
            res_model: 'garment.sample',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
            context: {
                default_state: 'new',
                create: true
            }
        });
    }
}

class SampleTreeRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.rpc = useService('rpc');
        this.notification = useService('notification');
        this.state.progressDetailStatus = []

        onMounted(() => {
            this.fetchAllProgressDetails();
        })
    }

    async fetchAllProgressDetails() {
        var ids = [];
        for (const record of this.props.list.records) {
            ids.push(record.resId)
        }

        if (!ids.length) return;
        try {
            const result = await this.rpc('/garment/sample/search_read', {
                domain: [['id', 'in', ids]],
                fields: ['id', 'progress_detail']
            });

            const mapping = [];
            for (const rec of result) {
                var progress_states = []
                
                const details = Array.isArray(rec.progress_detail)
                    ? rec.progress_detail
                    : (rec.progress_detail ? JSON.parse(rec.progress_detail) : []);
                for (const detail of details) {
                    progress_states.push(detail.state)
                }

                mapping.push({
                    id: rec.id,
                    states: progress_states
                })
            }
            this.state.progressDetailStatus = mapping;
        } catch (error) {
            this.notification.add(_t("Error loading sample progress"), { type: "danger" });
            console.error(error)
        }
    }

    getProgressStates(record) {
        return this.state.progressDetailStatus.find(item => item.id === record.resId)?.states || [];
    }

    getProgressBarClass(state) {
        if (state === 'not_started') {
            return 'progress-bar-not-started';
        } else if (state === 'in_progress') {
            return 'progress-bar-in-progress';
        } else {
            return 'progress-bar-completed';
        }
    }

    getProgressBarText(state) {
        if (state === 'not_started') {
            return 'Not Started';
        } else if (state === 'in_progress') {
            return 'In Progress';
        } else {
            return 'Completed';
        }
    }
    
    

    static recordRowTemplate = "garment.sample.SampleTreeRow";
}

// Register the custom list view
registry.category('views').add('sample_tree_view', {
    ...listView,
    Controller: CustomListController,
    Renderer: SampleTreeRenderer,
    buttonTemplate: 'garment_sample.create_button.buttons',
});




