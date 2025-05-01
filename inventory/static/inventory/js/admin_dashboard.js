document.addEventListener('DOMContentLoaded', function() {
    // --- ISSUED COMPONENTS SEARCH ---
    const issuedSearchInput = document.getElementById('issuedSearchInput');
    const issuedTable = document.querySelector('#issued .table tbody');
    const issuedRows = issuedTable ? issuedTable.getElementsByTagName('tr') : [];

    if (issuedSearchInput && issuedTable) {
        issuedSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();

            for (let row of issuedRows) {
                if (row.classList.contains('text-center')) continue;

                const component = row.cells[0].textContent.toLowerCase();
                const issuedTo = row.cells[1].textContent.toLowerCase();
                const quantity = row.cells[2].textContent.toLowerCase();
                const issueDate = row.cells[3].textContent.toLowerCase();
                const returnDeadline = row.cells[4].textContent.toLowerCase();
                const status = row.cells[5].textContent.toLowerCase();

                const matches = component.includes(searchTerm) ||
                              issuedTo.includes(searchTerm) ||
                              quantity.includes(searchTerm) ||
                              issueDate.includes(searchTerm) ||
                              returnDeadline.includes(searchTerm) ||
                              status.includes(searchTerm);

                row.style.display = matches ? '' : 'none';
            }

            // Show/hide "No results" message
            const noResultsRow = issuedTable.querySelector('.text-center');
            if (noResultsRow) {
                const hasVisibleRows = Array.from(issuedRows).some(row => row.style.display !== 'none');
                noResultsRow.style.display = hasVisibleRows ? 'none' : '';
            }
        });

        // Add search button functionality
        const issuedSearchButton = issuedSearchInput.nextElementSibling;
        if (issuedSearchButton) {
            issuedSearchButton.addEventListener('click', function() {
                issuedSearchInput.dispatchEvent(new Event('input'));
            });
        }

        // Add keyboard support
        issuedSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.dispatchEvent(new Event('input'));
            }
        });
    }
}); 