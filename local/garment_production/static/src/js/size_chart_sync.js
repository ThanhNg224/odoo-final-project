document.addEventListener('DOMContentLoaded', function () {
    const button = document.querySelector('button[name="generate_order_lines_from_size_chart"]');
    if (!button) return;

    // console.log("🔥 JS collectSizeChartData loaded");

    button.addEventListener('click', function () {
        const table = document.querySelector('.pmc-table');
        if (!table) {
            console.warn("⛔ pmc-table not found");
            return;
        }

        const headerCells = table.querySelectorAll('thead tr th');
        const sizes = Array.from(headerCells).slice(1).map(cell => cell.innerText.trim());

        const data = {}; // 💥 THIS MUST BE A DICTIONARY!

        const bodyRows = table.querySelectorAll('tbody tr');
        for (let row of bodyRows) {
            const cells = row.querySelectorAll('td');
            const color = cells[0].innerText.trim();
            data[color] = {};

            for (let i = 1; i < cells.length; i++) {
                const input = cells[i].querySelector('input');
                const qty = input ? parseInt(input.value || '0') : 0;
                data[color][sizes[i - 1]] = qty;
            }
        }

        const field = document.querySelector('[name="size_chart_data"]');
        if (field) {
            field.value = JSON.stringify(data);
            // console.log("✅ size_chart_data updated:", field.value);
        }
    });
});
