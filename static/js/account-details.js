// Account Details and Inline Editing Module

// Load asset details
function loadAssetDetails(accountNumber) {
    if (!accountNumber || accountNumber === 'null' || accountNumber === 'undefined') {
        console.error('Invalid account number:', accountNumber);
        document.getElementById('asset-details-content').innerHTML = 
            '<div class="alert alert-danger">Invalid account identifier</div>';
        return;
    }
    
    fetch(`/api/asset/${accountNumber}/history?period=${AppState.currentAssetPeriod}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            displayAssetDetails(data);
        })
        .catch(error => {
            console.error('Error loading asset details:', error);
            document.getElementById('asset-details-content').innerHTML = 
                `<div class="alert alert-danger">Failed to load asset details: ${error.message}</div>`;
        });
}

// Display asset details
function displayAssetDetails(data) {
    const container = document.getElementById('asset-details-content');
    
    if (!data || !data.account) {
        container.innerHTML = '<div class="alert alert-danger">Invalid asset data</div>';
        return;
    }
    
    AppState.currentAssetData = data;
    const account = data.account;
    
    document.querySelector('.asset-period-dropdown').style.display = 'none';
    
    const detailTitle = document.getElementById('detail-title');
    const headerContainer = detailTitle.parentElement;
    
    const isArchived = account.archived === true || account.archived === 1;
    
    if (!headerContainer.querySelector('.asset-action-buttons')) {
        const actionButtons = document.createElement('div');
        actionButtons.className = 'asset-action-buttons d-flex gap-2';
        headerContainer.appendChild(actionButtons);
    }
    
    const actionButtonsContainer = headerContainer.querySelector('.asset-action-buttons');
    if (isArchived) {
        actionButtonsContainer.innerHTML = `
            <button class="btn btn-outline-info btn-sm" id="restore-btn" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">
                <i class="bi bi-arrow-counterclockwise"></i> Restore
            </button>
            <button class="btn btn-outline-danger btn-sm" id="delete-btn" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">
                <i class="bi bi-trash"></i> Delete
            </button>
        `;
    } else {
        actionButtonsContainer.innerHTML = `
            <button class="btn btn-outline-warning btn-sm" id="archive-btn" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">
                <i class="bi bi-archive"></i> Archive
            </button>
            <button class="btn btn-outline-danger btn-sm" id="delete-btn" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">
                <i class="bi bi-trash"></i> Delete
            </button>
        `;
    }
    
    const restoreBtn = document.getElementById('restore-btn');
    const archiveBtn = document.getElementById('archive-btn');
    const deleteBtn = document.getElementById('delete-btn');
    
    if (restoreBtn) restoreBtn.onclick = () => restoreAccount(account.id);
    if (archiveBtn) archiveBtn.onclick = () => archiveAccount(account.id);
    deleteBtn.onclick = () => deleteAccount(account.id);
    
    // Get last_updated from the data object (not account object)
    const lastUpdated = data.last_updated || account.last_updated || 'N/A';
    const isLiability = AppState.currentAccountType === 'liabilities' || account.current_value < 0;
    const valueClass = isLiability ? 'text-danger' : 'text-success';
    
    const growthPercentage = account.growth_percentage || 0;
    const growthClass = growthPercentage >= 0 ? 'text-success' : 'text-danger';
    const growthPrefix = growthPercentage >= 0 ? '+' : '';
    const growthText = growthPercentage !== 0 ? `${growthPrefix}${growthPercentage.toFixed(2)}%` : '0%';
    
    const editableClass = isArchived ? '' : 'editable-field';
    const editableCursor = isArchived ? 'cursor: default;' : 'cursor: pointer;';
    const editableTitle = isArchived ? 'Archived accounts cannot be edited. Restore to edit.' : 'Click to edit';
    const archivedBadge = isArchived ? '<span class="badge bg-warning text-dark ms-2">ARCHIVED</span>' : '';
    
    // Prepare note display
    let noteDisplay = 'N/A';
    if (account.note) {
        if (account.note.length > 50) {
            const truncated = account.note.substring(0, 50);
            noteDisplay = `${truncated}... <span style="color: var(--accent-primary); cursor: pointer; text-decoration: underline;" class="view-full-note">[View full]</span>`;
        } else {
            noteDisplay = account.note;
        }
    }
    
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; height: 100%; min-height: 0;">
            ${isArchived ? '<div class="alert alert-warning mb-2"><i class="bi bi-exclamation-triangle"></i> This account is archived. All fields are read-only until restored.</div>' : ''}
            <div class="asset-detail-grid">
                <div class="asset-detail-item">
                    <label>Name</label>
                    <span class="${editableClass}" data-field="name" data-account-id="${account.id}" style="${editableCursor}" title="${editableTitle}">${account.name || 'N/A'}${archivedBadge}</span>
                </div>
                <div class="asset-detail-item">
                    <label>Notes</label>
                    <span class="note-preview ${!isArchived ? 'note-editable' : ''}" data-field="note" data-account-id="${account.id}" style="${editableCursor}" title="${isArchived ? 'Archived accounts cannot be edited' : 'Click to view/edit note'}">
                        ${noteDisplay}
                    </span>
                </div>
                <div class="asset-detail-item">
                    <label>Current Value</label>
                    <div class="d-flex align-items-center gap-2">
                        <span class="${editableClass} ${valueClass}" data-field="current_value" data-account-id="${account.id}" style="${editableCursor}" title="${editableTitle}">${account.current_value ? Math.abs(account.current_value).toFixed(2) : 'N/A'}</span>
                        <span class="${editableClass} currency-dropdown-field" data-field="currency" data-account-id="${account.id}" style="font-size: 0.9em; color: #6c757d; ${editableCursor}" title="${editableTitle}">${account.currency || 'N/A'}</span>
                    </div>
                </div>
                <div class="asset-detail-item">
                    <label>Growth (${data.period || 'period'})</label>
                    <span class="${growthClass}" style="font-weight: 600;">${growthText}</span>
                </div>
                <div class="asset-detail-item">
                    <label>Last Updated</label>
                    <span>${lastUpdated}</span>
                </div>
                <div class="asset-detail-item">
                    <label>Tags</label>
                    <span class="${editableClass}" data-field="tags" data-account-id="${account.id}" style="${editableCursor}" title="${editableTitle}">
                        ${account.tags && account.tags.length > 0 
                            ? account.tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('') 
                            : '<span class="text-muted">No tags</span>'}
                    </span>
                </div>
            </div>
            <div class="asset-chart-container">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0" style="font-weight: 600; color: var(--text-primary);">History</h6>
                    <select id="inline-asset-period-select" class="form-select form-select-sm" style="width: auto; min-width: 150px;">
                        <option value="week">1 Week</option>
                        <option value="month">1 Month</option>
                        <option value="3months">3 Months</option>
                        <option value="6months">6 Months</option>
                        <option value="ytd" ${data.period === 'ytd' ? 'selected' : ''}>Year to Date</option>
                        <option value="year">1 Year</option>
                        <option value="2years">2 Years</option>
                        <option value="3years">3 Years</option>
                        <option value="4years">4 Years</option>
                        <option value="5years">5 Years</option>
                        <option value="max">Max</option>
                    </select>
                </div>
                <div style="flex: 1; min-height: 0; position: relative;">
                    <canvas id="assetChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    setupEditableFields();
    
    const inlinePeriodSelect = document.getElementById('inline-asset-period-select');
    if (inlinePeriodSelect) {
        inlinePeriodSelect.addEventListener('change', function() {
            AppState.currentAssetPeriod = this.value;
            if (AppState.selectedAssetId) {
                loadAssetDetails(AppState.selectedAssetId);
            }
        });
    }
    
    const history = data.history || [];
    
    if (history.length > 0) {
        setTimeout(() => {
            createAssetChart(history, account.currency || AppState.currentCurrency);
        }, 100);
    } else {
        container.querySelector('.asset-chart-container').innerHTML = 
            '<p class="text-muted text-center p-3">No historical data available for this period</p>';
    }
}

// Setup editable fields
function setupEditableFields() {
    document.querySelectorAll('.editable-field').forEach(field => {
        field.style.cursor = 'pointer';
        field.title = 'Click to edit';
        
        field.addEventListener('click', function() {
            const fieldName = this.dataset.field;
            const accountId = this.dataset.accountId;
            const currentValue = this.textContent.trim();
            
            if (this.querySelector('input')) return;
            
            if (fieldName === 'tags') {
                editTagsField(accountId);
                return;
            }
            
            makeFieldEditable(this, fieldName, accountId, currentValue);
        });
    });
}

// Make a field editable
function makeFieldEditable(element, fieldName, accountId, currentValue) {
    const originalContent = element.innerHTML;
    let inputValue = currentValue;
    
    if (fieldName === 'current_value') {
        inputValue = currentValue.replace(/[^\d.-]/g, '');
    }
    
    let inputElement;
    if (fieldName === 'currency') {
        inputElement = document.createElement('select');
        inputElement.className = 'form-select form-select-sm';
        
        if (AppState.currencyData && AppState.currencyData.list && AppState.currencyData.list.length > 0) {
            inputElement.innerHTML = '<option value="">Select currency...</option>';
            AppState.currencyData.list.forEach(curr => {
                const option = document.createElement('option');
                option.value = curr.code;
                option.textContent = `${curr.code} - ${curr.name}`;
                if (curr.code === currentValue) option.selected = true;
                inputElement.appendChild(option);
            });
        }
    } else {
        inputElement = document.createElement('input');
        inputElement.type = fieldName === 'current_value' ? 'number' : 'text';
        inputElement.className = 'form-control form-control-sm';
        inputElement.value = inputValue;
        
        if (fieldName === 'current_value') {
            inputElement.step = '0.01';
        }
    }
    
    element.innerHTML = '';
    element.appendChild(inputElement);
    
    inputElement.focus();
    if (inputElement.select) inputElement.select();
    
    const saveChanges = () => {
        let newValue = inputElement.value.trim();
        
        if (fieldName === 'currency') {
            newValue = newValue.toUpperCase();
            if (!/^[A-Z]{3}$/.test(newValue)) {
                element.innerHTML = originalContent;
                setupEditableFields();
                return;
            }
        }
        
        if (newValue !== inputValue) {
            updateAccountField(accountId, fieldName, newValue)
                .then(success => {
                    if (success) {
                        loadAccounts();
                        loadAssetDetails(accountId);
                    } else {
                        element.innerHTML = originalContent;
                        setupEditableFields();
                    }
                })
                .catch(error => {
                    console.error('Error updating field:', error);
                    element.innerHTML = originalContent;
                    setupEditableFields();
                });
        } else {
            element.innerHTML = originalContent;
            setupEditableFields();
        }
    };
    
    const cancelChanges = () => {
        element.innerHTML = originalContent;
        setupEditableFields();
    };
    
    inputElement.addEventListener('blur', saveChanges);
    inputElement.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            inputElement.removeEventListener('blur', saveChanges); // Prevent duplicate save
            saveChanges();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelChanges();
        }
    });
}

// Update account field via API
async function updateAccountField(accountNumber, fieldName, fieldValue) {
    try {
        const accountId = parseInt(accountNumber);
        const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
        const account = accounts.find(acc => acc.id === accountId);
        
        if (!account) {
            console.error('Account not found:', accountId);
            return false;
        }
        
        let convertedValue = fieldValue;
        if (fieldName === 'current_value') {
            convertedValue = parseFloat(fieldValue);
            if (isNaN(convertedValue)) {
                alert('Please enter a valid number for the value');
                return false;
            }
        } else if (fieldName === 'currency') {
            if (!/^[A-Z]{3}$/.test(fieldValue.toUpperCase())) {
                alert('Currency must be a 3-letter code (e.g., USD, EUR, GBP)');
                return false;
            }
            convertedValue = fieldValue.toUpperCase();
        }
        
        const response = await fetch(`/api/accounts/${account.id}/field`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.sessionData.csrfToken
            },
            body: JSON.stringify({
                field: fieldName,
                value: convertedValue
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessToast('Field updated successfully!');
            
            if (fieldName === 'current_value') {
                loadAccounts();
                if (AppState.chart) {
                    AppState.chart.destroy();
                    AppState.chart = null;
                }
                setTimeout(() => loadChart(AppState.currentPeriod), 500);
            }
            
            return true;
        } else {
            alert('Error updating field: ' + (result.error || 'Unknown error'));
            return false;
        }
    } catch (error) {
        console.error('Error updating field:', error);
        alert('Error updating field: ' + error.message);
        return false;
    }
}

// Delete, Archive, Restore functions
async function deleteAccount(accountNumber) {
    const accountId = parseInt(accountNumber);
    const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
    const account = accounts.find(acc => acc.id === accountId);
    
    if (!account) {
        showErrorToast('Account not found');
        return;
    }
    
    window.currentModalAccountId = account.id;
    document.getElementById('delete-account-name').textContent = account.name;
    const modalEl = document.getElementById('deleteConfirmModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function archiveAccount(accountNumber) {
    const accountId = parseInt(accountNumber);
    const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
    const account = accounts.find(acc => acc.id === accountId);
    
    if (!account) {
        showErrorToast('Account not found');
        return;
    }
    
    window.currentModalAccountId = account.id;
    document.getElementById('archive-account-name').textContent = account.name;
    const modalEl = document.getElementById('archiveConfirmModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function restoreAccount(accountNumber) {
    const accountId = parseInt(accountNumber);
    const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
    const account = accounts.find(acc => acc.id === accountId);
    
    if (!account) {
        showErrorToast('Account not found');
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/${account.id}/restore`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.sessionData.csrfToken
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessToast('Account restored successfully! Current value is set to 0. You can update it now.');
            loadAccounts();
            loadChart(AppState.currentPeriod);
            setTimeout(() => loadAssetDetails(accountNumber), 300);
        } else {
            showErrorToast('Error restoring account: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error restoring account:', error);
        showErrorToast('Error restoring account: ' + error.message);
    }
}

// Initialize note modal handler
function initializeNoteModal() {
    // Blur any focused element when modal is about to hide (prevents aria-hidden warning)
    const modalEl = document.getElementById('editNoteModal');
    if (modalEl) {
        modalEl.addEventListener('hide.bs.modal', function() {
            if (document.activeElement && document.activeElement.blur) {
                document.activeElement.blur();
            }
        });
    }
    
    // Handle "View full" link clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-full-note')) {
            e.preventDefault();
            e.stopPropagation();
            
            const noteSpan = e.target.closest('.note-preview');
            if (!noteSpan) return;
            
            const accountId = noteSpan.dataset.accountId;
            const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
            const account = accounts.find(acc => acc.id === parseInt(accountId));
            
            if (!account) return;
            
            // Populate modal
            document.getElementById('edit-note-textarea').value = account.note || '';
            document.getElementById('edit-note-account-id').value = accountId;
            
            // Show modal
            const modalEl = document.getElementById('editNoteModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            
            return; // Prevent further event handling
        }
    }, true); // Use capture phase to catch the event first
    
    // Handle note span clicks (if not archived and not clicking on "View full")
    document.addEventListener('click', function(e) {
        const noteSpan = e.target.closest('.note-preview.note-editable');
        if (!noteSpan) return;
        
        // Don't handle if clicking the "View full" link
        if (e.target.classList.contains('view-full-note')) return;
        
        const accountId = noteSpan.dataset.accountId;
        const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
        const account = accounts.find(acc => acc.id === parseInt(accountId));
        
        if (!account || account.archived) return;
        
        // Populate modal
        document.getElementById('edit-note-textarea').value = account.note || '';
        document.getElementById('edit-note-account-id').value = accountId;
        
        // Show modal
        const modalEl = document.getElementById('editNoteModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    });
    
    // Handle save button
    const saveBtn = document.getElementById('save-note-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async function() {
            const accountId = document.getElementById('edit-note-account-id').value;
            const noteText = document.getElementById('edit-note-textarea').value;
            
            if (!accountId) return;
            
            try {
                const response = await fetch(`/api/accounts/${accountId}/field`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.sessionData.csrfToken
                    },
                    body: JSON.stringify({ 
                        field: 'note',
                        value: noteText 
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccessToast('Note updated successfully');
                    
                    // Blur the button to remove focus before hiding modal
                    saveBtn.blur();
                    
                    // Close modal
                    const modalEl = document.getElementById('editNoteModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    
                    // Reload account details
                    loadAccounts();
                    setTimeout(() => loadAssetDetails(accountId), 300);
                } else {
                    showErrorToast('Error updating note: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error updating note:', error);
                showErrorToast('Error updating note: ' + error.message);
            }
        });
    }
}

// Expose functions globally
window.loadAssetDetails = loadAssetDetails;
window.displayAssetDetails = displayAssetDetails;
window.setupEditableFields = setupEditableFields;
window.makeFieldEditable = makeFieldEditable;
window.updateAccountField = updateAccountField;
window.deleteAccount = deleteAccount;
window.archiveAccount = archiveAccount;
window.restoreAccount = restoreAccount;
window.initializeNoteModal = initializeNoteModal;
