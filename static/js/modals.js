// Modals Management Module

// Initialize Add Asset Modal
function initializeAddAssetModal() {
    const modal = document.getElementById('addAssetModal');
    const form = document.getElementById('add-asset-form');
    const submitBtn = document.getElementById('submit-asset-btn');
    const errorDiv = document.getElementById('add-asset-error');
    const currencySelect = document.getElementById('asset-currency');
    const valueSignToggle = document.getElementById('value-sign-toggle');
    const valueInput = document.getElementById('asset-value');
    
    // Add hide event listener to prevent aria-hidden warning
    modal.addEventListener('hide.bs.modal', function() {
        if (document.activeElement && modal.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });
    
    // Handle +/- toggle
    let isPositive = true;
    valueSignToggle.addEventListener('click', function() {
        isPositive = !isPositive;
        valueSignToggle.textContent = isPositive ? '+' : '-';
        valueSignToggle.className = isPositive ? 'btn btn-outline-success' : 'btn btn-outline-danger';
    });
    
    // Load currencies into modal dropdown
    modal.addEventListener('show.bs.modal', function() {
        // Reset +/- toggle to positive
        isPositive = true;
        valueSignToggle.textContent = '+';
        valueSignToggle.className = 'btn btn-outline-success';
        
        // Populate currency dropdown
        if (AppState.currencyData && AppState.currencyData.list && AppState.currencyData.list.length > 0) {
            currencySelect.innerHTML = '<option value="">Select currency...</option>';
            AppState.currencyData.list.forEach(curr => {
                const option = document.createElement('option');
                option.value = curr.code;
                option.textContent = `${curr.code} - ${curr.name}`;
                if (curr.code === AppState.currentCurrency) {
                    option.selected = true;
                }
                currencySelect.appendChild(option);
            });
        } else {
            fetch('/api/currencies')
                .then(response => response.json())
                .then(data => {
                    currencySelect.innerHTML = '<option value="">Select currency...</option>';
                    if (data.all && data.all.length > 0) {
                        data.all.forEach(curr => {
                            const option = document.createElement('option');
                            option.value = curr.code;
                            option.textContent = `${curr.code} - ${curr.name}`;
                            if (curr.code === AppState.currentCurrency) {
                                option.selected = true;
                            }
                            currencySelect.appendChild(option);
                        });
                    }
                })
                .catch(error => console.error('Failed to load currencies:', error));
        }
        
        // Reset form
        form.reset();
        errorDiv.style.display = 'none';
        
        // Reset history input handler
        if (window.historyInputHandler) {
            window.historyInputHandler.reset();
        }
        
        // Set default currency to current view currency after reset
        setTimeout(() => {
            if (currencySelect.value === '') {
                currencySelect.value = AppState.currentCurrency;
            }
        }, 100);
    });
    
    // Handle form submission
    submitBtn.addEventListener('click', function() {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding...';
        errorDiv.style.display = 'none';
        
        // Validate currency
        const currencyInput = document.getElementById('asset-currency');
        const currency = currencyInput.value.trim().toUpperCase();
        if (currency && !/^[A-Z]{3}$/.test(currency)) {
            showErrorToast('Currency must be a 3-letter code (e.g., USD, EUR, GBP)');
            currencyInput.value = AppState.currentCurrency;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Add Asset';
            return;
        }
        
        // Gather form data with sign applied
        let value = parseFloat(document.getElementById('asset-value').value);
        if (!isPositive) {
            value = -Math.abs(value);
        }
        
        const formData = {
            name: document.getElementById('asset-name').value.trim(),
            current_value: value,
            currency: currency || AppState.currentCurrency,
            tags: JSON.parse(document.getElementById('asset-tags-hidden').value || '[]'),
            term_length: parseFloat(document.getElementById('asset-liquidity').value),
            ownership_ratio: parseFloat(document.getElementById('asset-ownership').value) / 100
        };
        
        // Add history data if available
        if (window.historyInputHandler) {
            const historyData = window.historyInputHandler.getHistoryData();
            if (historyData && historyData.length > 0) {
                formData.history = historyData;
            }
        }
        
        // Validate ownership ratio
        if (formData.ownership_ratio < 0 || formData.ownership_ratio > 1) {
            showError('Ownership percentage must be between 0 and 100');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Add Asset';
            return;
        }
        
        // Submit to API
        fetch('/api/accounts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.sessionData.csrfToken
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Add Asset';
            } else {
                // Success - close modal and reload accounts
                bootstrap.Modal.getInstance(modal).hide();
                loadAccounts();
                loadChart(AppState.currentPeriod);
                
                showSuccessToast('Asset added successfully!');
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Add Asset';
            }
        })
        .catch(error => {
            showError('Failed to add asset: ' + error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Add Asset';
        });
    });
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

// Set up modal confirmation handlers
function setupModalHandlers() {
    const deleteModalEl = document.getElementById('deleteConfirmModal');
    const archiveModalEl = document.getElementById('archiveConfirmModal');
    
    deleteModalEl.addEventListener('hide.bs.modal', function() {
        if (document.activeElement && deleteModalEl.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });
    
    archiveModalEl.addEventListener('hide.bs.modal', function() {
        if (document.activeElement && archiveModalEl.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });
    
    // Delete confirmation
    document.getElementById('confirm-delete-btn').addEventListener('click', async function() {
        if (!window.currentModalAccountId) return;
        
        const modalEl = document.getElementById('deleteConfirmModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        try {
            const response = await fetch(`/api/accounts/${window.currentModalAccountId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': window.sessionData.csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccessToast('Account deleted successfully!');
                loadAccounts();
                loadChart(AppState.currentPeriod);
                document.getElementById('asset-details-content').innerHTML = 
                    `<p class="text-muted text-center">Select an asset from the list to view details</p>`;
                document.querySelector('.asset-period-dropdown').style.display = 'none';
            } else {
                showErrorToast('Error deleting account: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting account:', error);
            showErrorToast('Error deleting account: ' + error.message);
        }
        
        window.currentModalAccountId = null;
    });
    
    // Archive confirmation
    document.getElementById('confirm-archive-btn').addEventListener('click', async function() {
        if (!window.currentModalAccountId) return;
        
        const modalEl = document.getElementById('archiveConfirmModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        try {
            const response = await fetch(`/api/accounts/${window.currentModalAccountId}/archive`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.sessionData.csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccessToast('Account archived successfully!');
                loadAccounts();
                loadChart(AppState.currentPeriod);
                document.getElementById('asset-details-content').innerHTML = 
                    `<p class="text-muted text-center">Select an asset from the list to view details</p>`;
                document.querySelector('.asset-period-dropdown').style.display = 'none';
            } else {
                showErrorToast('Error archiving account: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error archiving account:', error);
            showErrorToast('Error archiving account: ' + error.message);
        }
        
        window.currentModalAccountId = null;
    });
}

// Initialize modal account ID storage
window.currentModalAccountId = null;

// Expose functions globally
window.initializeAddAssetModal = initializeAddAssetModal;
window.setupModalHandlers = setupModalHandlers;
