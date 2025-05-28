/** @odoo-module **/
import { ListController } from '@web/views/list/list_controller';
import { listView } from '@web/views/list/list_view';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';

export class CustomListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService('action');
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

// Register the custom list view
registry.category('views').add('custom_create_button', {
    ...listView,
    Controller: CustomListController,
    buttonTemplate: 'garment_sample.create_button.buttons',
});