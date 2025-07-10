/** @odoo-module **/
import { ListController } from '@web/views/list/list_controller';
import { listView } from '@web/views/list/list_view';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';

export class OrderListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService('action');
    }

    onCreateButtonClick = () => {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Create Garment Order',
            res_model: 'garment.order',
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

// Register the order list view
registry.category('views').add('order_create_button', {
    ...listView,
    Controller: OrderListController,
    buttonTemplate: 'garment_order.create_button.buttons',
});