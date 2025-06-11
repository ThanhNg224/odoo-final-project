/* filepath: c:\Users\hp\OneDrive\Documents\odoo-final-project\local\garment_production\static\src\js\production_enhancements.js */

odoo.define('garment_production.production_enhancements', function (require) {
"use strict";

var FormController = require('web.FormController');
var ListController = require('web.ListController');
var KanbanController = require('web.KanbanController');

// Add smooth transitions and loading states
FormController.include({
    init: function() {
        this._super.apply(this, arguments);
        if (this.modelName === 'production.order') {
            this._addProductionEnhancements();
        }
    },
    
    _addProductionEnhancements: function() {
        // Add loading shimmer effect
        this.$el.on('click', '.o_form_button_save', function() {
            $(this).addClass('loading-shimmer');
            setTimeout(() => {
                $(this).removeClass('loading-shimmer');
            }, 1500);
        });
        
        // Add smooth scroll to errors
        this.$el.on('invalid_fields', function() {
            $('html, body').animate({
                scrollTop: $('.o_field_invalid').first().offset().top - 100
            }, 500);
        });
    }
});

// Enhanced Kanban animations
KanbanController.include({
    init: function() {
        this._super.apply(this, arguments);
        if (this.modelName === 'production.order') {
            this._addKanbanAnimations();
        }
    },
    
    _addKanbanAnimations: function() {
        // Add stagger animation to cards
        setTimeout(() => {
            $('.production_kanban_card').each(function(index) {
                $(this).css({
                    'animation-delay': (index * 0.1) + 's',
                    'animation-name': 'slideInUp',
                    'animation-duration': '0.5s',
                    'animation-fill-mode': 'both'
                });
            });
        }, 100);
    }
});

});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.o_production_form {
    animation: fadeIn 0.5s ease-in;
}

.production_kanban_card {
    transition: all 0.3s ease;
}

.production_kanban_card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
`;
document.head.appendChild(style);