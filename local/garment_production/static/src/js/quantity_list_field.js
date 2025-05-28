/**
 * Simple JavaScript to enhance the quantity list text field
 * by adding a table preview below it
 */
$(document).ready(function() {
    // Function to create and update the table display
    function updateQuantityListTable() {
        // Find all quantity_list_field textareas
        var textareas = document.querySelectorAll('.quantity_list_field textarea');
        
        textareas.forEach(function(textarea) {
            // Check if table already exists, if not create it
            var tableContainer = textarea.parentNode.nextElementSibling;
            if (!tableContainer || !tableContainer.classList.contains('quantity-list-table-container')) {
                // Create container
                tableContainer = document.createElement('div');
                tableContainer.className = 'quantity-list-table-container mt-3';
                
                // Create title
                var title = document.createElement('h5');
                title.className = 'text-center mb-3';
                title.textContent = 'Preview';
                tableContainer.appendChild(title);
                
                // Create table
                var table = document.createElement('table');
                table.className = 'table table-bordered table-striped';
                tableContainer.appendChild(table);
                
                // Insert after textarea's parent
                textarea.parentNode.parentNode.insertBefore(tableContainer, textarea.parentNode.nextSibling);
            }
            
            // Update table content
            updateTableFromJSON(textarea.value, tableContainer.querySelector('table'));
        });
    }
    
    // Function to parse JSON and update the table
    function updateTableFromJSON(jsonStr, table) {
        if (!table) return;
        
        try {
            // Parse the JSON string
            var data = JSON.parse(jsonStr);
            
            if (!Array.isArray(data) || data.length === 0) {
                table.innerHTML = '<tr><td class="text-center text-muted">No data available</td></tr>';
                return;
            }
            
            // Create table HTML
            var html = '<thead><tr>';
            
            // Add headers
            if (data[0] && Array.isArray(data[0])) {
                data[0].forEach(function(header) {
                    html += '<th class="text-center">' + (header || '') + '</th>';
                });
            } else {
                html += '<th class="text-center">Size</th><th class="text-center">Quantity</th>';
            }
            
            html += '</tr></thead><tbody>';
            
            // Add data rows (skip header)
            var hasRows = false;
            for (var i = 1; i < data.length; i++) {
                var row = data[i];
                if (!row || !Array.isArray(row)) continue;
                
                if (row[0] || row[1]) {
                    hasRows = true;
                    html += '<tr>';
                    row.forEach(function(cell) {
                        html += '<td class="text-center">' + (cell || '') + '</td>';
                    });
                    html += '</tr>';
                }
            }
            
            // If no data rows, show empty message
            if (!hasRows) {
                html += '<tr><td colspan="' + (data[0] ? data[0].length : 2) + '" class="text-center text-muted">No sizes defined yet</td></tr>';
            }
            
            html += '</tbody>';
            table.innerHTML = html;
            
        } catch (e) {
            console.error('Error parsing quantity list JSON:', e);
            table.innerHTML = '<tr><td class="text-center text-danger">Invalid JSON format</td></tr>';
        }
    }
    
    // Initial display when document is loaded
    updateQuantityListTable();
    
    // Update when the textarea changes
    $(document).on('input', '.quantity_list_field textarea', function() {
        var textarea = this;
        var tableContainer = textarea.parentNode.parentNode.querySelector('.quantity-list-table-container');
        if (tableContainer) {
            var table = tableContainer.querySelector('table');
            updateTableFromJSON(textarea.value, table);
        }
    });
    
    // Update when switching tabs
    $(document).on('click', '.nav-tabs a', function() {
        setTimeout(updateQuantityListTable, 200);
    });
}); 