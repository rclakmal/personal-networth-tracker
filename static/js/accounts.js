// Account Management Module

// Load accounts data from API
function loadAccounts() {
    const showArchived = document.getElementById('show-archived-check').checked;
    const includeArchivedParam = showArchived ? 'include_archived=true' : 'include_archived=false';
    
    fetch(`/api/accounts/${AppState.currentCurrency}?sort=${AppState.currentSort}&${includeArchivedParam}`)
        .then(response => response.json())
        .then(data => {
            // Update summary metrics with compact formatting
            const networthEl = document.getElementById('current-networth');
            const assetsEl = document.getElementById('total-assets');
            const liabilitiesEl = document.getElementById('total-liabilities');
            
            // Set compact text
            networthEl.textContent = formatCompactNumber(data.net_worth, AppState.currentCurrency);
            assetsEl.textContent = formatCompactNumber(data.total_assets, AppState.currentCurrency);
            liabilitiesEl.textContent = formatCompactNumber(data.total_liabilities, AppState.currentCurrency);
            
            // Add tooltips with exact values
            networthEl.title = formatCurrency(data.net_worth, AppState.currentCurrency);
            assetsEl.title = formatCurrency(data.total_assets, AppState.currentCurrency);
            liabilitiesEl.title = formatCurrency(data.total_liabilities, AppState.currentCurrency);
            
            // Store accounts data
            AppState.accountsData = {
                assets: [...data.savings, ...data.equity],
                liabilities: data.credit
            };
            
            // Display asset list
            displayAssetList();
        })
        .catch(error => console.error('Error loading accounts:', error));
}

// Update toggle button states
function updateToggleButtons() {
    const assetsToggle = document.getElementById('assets-toggle');
    const liabilitiesToggle = document.getElementById('liabilities-toggle');
    const detailTitle = document.getElementById('detail-title');
    
    assetsToggle.classList.toggle('active', AppState.currentAccountType === 'assets');
    liabilitiesToggle.classList.toggle('active', AppState.currentAccountType === 'liabilities');
    
    // Update detail title based on current type
    detailTitle.textContent = AppState.currentAccountType === 'liabilities' ? 'Liability Details' : 'Asset Details';
}

// Display asset list
function displayAssetList() {
    const container = document.getElementById('asset-list');
    const accounts = AppState.accountsData[AppState.currentAccountType] || [];
    
    container.innerHTML = '';
    
    if (accounts.length === 0) {
        container.innerHTML = `<p class="text-muted text-center p-3">No ${AppState.currentAccountType} found</p>`;
        // Hide period selector and clear details when no assets
        document.querySelector('.asset-period-dropdown').style.display = 'none';
        const placeholderText = AppState.currentAccountType === 'liabilities' ? 
            'Select a liability from the list to view details' : 
            'Select an asset from the list to view details';
        document.getElementById('asset-details-content').innerHTML = 
            `<p class="text-muted text-center">${placeholderText}</p>`;
        return;
    }
    
    // Accounts are already sorted by backend
    accounts.forEach((account, index) => {
        const item = createAssetListItem(account);
        container.appendChild(item);
        
        // Select first item by default on initial load or when switching types
        if (index === 0 && (!AppState.selectedAssetId || !accounts.find(a => a.id === AppState.selectedAssetId))) {
            setTimeout(() => selectAsset(account), 50);
        }
    });
}

// Create asset list item
function createAssetListItem(account) {
    const item = document.createElement('div');
    item.className = 'asset-list-item';
    
    if (account.archived) {
        item.classList.add('archived');
    }
    
    const accountId = account.id;
    if (AppState.selectedAssetId === accountId) {
        item.classList.add('active');
    }
    
    const isLiability = account.current_value < 0;
    const valueClass = (AppState.currentAccountType === 'liabilities' || isLiability) ? 'text-danger' : 'text-success';
    
    const archivedLabel = account.archived ? '<span class="badge bg-warning text-dark ms-1">Archived</span>' : '';
    
    // Display tags (multiple tags support)
    const tagsHTML = account.tags && account.tags.length > 0 
        ? account.tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('') 
        : '<span class="text-muted" style="font-size: 0.75rem;">No tags</span>';
    
    // Format value with compact notation and tooltip
    const exactValue = formatCurrency(account.value, AppState.currentCurrency);
    const compactValue = formatCompactNumber(account.value, AppState.currentCurrency);
    
    item.innerHTML = `
        <div class="asset-item-info">
            <div class="asset-item-name">${account.name}${archivedLabel}</div>
            <div class="asset-item-tag">
                ${tagsHTML}
            </div>
        </div>
        <div class="asset-item-value ${valueClass}" title="${exactValue}" style="cursor: help;">
            ${compactValue}
        </div>
    `;
    
    item.onclick = () => selectAsset(account);
    
    return item;
}

// Select an asset
function selectAsset(account) {
    const accountId = account.id;
    AppState.selectedAssetId = accountId;
    
    // Update active state in list
    document.querySelectorAll('.asset-list-item').forEach((item, index) => {
        item.classList.remove('active');
        const currentAccount = AppState.accountsData[AppState.currentAccountType][index];
        if (currentAccount && currentAccount.id === accountId) {
            item.classList.add('active');
        }
    });
    
    // Load asset details
    loadAssetDetails(accountId);
}

// Expose functions globally
window.loadAccounts = loadAccounts;
window.displayAssetList = displayAssetList;
window.updateToggleButtons = updateToggleButtons;
window.selectAsset = selectAsset;
