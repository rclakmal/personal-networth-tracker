// Main Application Initialization

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Wait for currencies to load before loading accounts
    window.onCurrenciesLoaded = function() {
        const currencySelector = document.getElementById('currency-selector');
        if (currencySelector) {
            AppState.currentCurrency = currencySelector.value || (window.sessionData ? window.sessionData.currency : 'EUR');
            
            // Save currency preference
            currencySelector.addEventListener('change', async function() {
                const newCurrency = this.value.trim().toUpperCase();
                
                // Validate currency format
                if (!/^[A-Z]{3}$/.test(newCurrency)) {
                    this.value = AppState.currentCurrency; // Reset to current currency
                    return;
                }
                
                // Only update if the currency is different
                if (newCurrency !== AppState.currentCurrency) {
                    try {
                        const response = await fetch('/api/user/currency', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': window.sessionData.csrfToken
                            },
                            body: JSON.stringify({ currency: newCurrency })
                        });

                        const data = await response.json();
                        
                        if (response.ok && data.success) {
                            AppState.currentCurrency = newCurrency;
                            window.sessionData.currency = newCurrency;
                            loadAccounts();
                            loadChart(AppState.currentPeriod);
                            showSuccessToast('Currency preference updated successfully');
                        } else {
                            this.value = AppState.currentCurrency; // Reset to current currency
                        }
                    } catch (error) {
                        console.error('Error updating currency preference:', error);
                        this.value = AppState.currentCurrency; // Reset to current currency
                    }
                }
            });
        }
        loadAccounts();
        loadChart('ytd');
    };
    
    // If currencies are already loaded, proceed
    if (AppState.currencyData && AppState.currencyData.loaded) {
        window.onCurrenciesLoaded();
    }
    
    // Time period selector
    document.getElementById('time-period-select').addEventListener('change', function() {
        AppState.currentPeriod = this.value;
        loadChart(AppState.currentPeriod);
    });
    
    // Assets/Liabilities toggle
    document.getElementById('assets-toggle').addEventListener('click', function() {
        AppState.currentAccountType = 'assets';
        updateToggleButtons();
        displayAssetList();
    });
    
    document.getElementById('liabilities-toggle').addEventListener('click', function() {
        AppState.currentAccountType = 'liabilities';
        updateToggleButtons();
        displayAssetList();
    });
    
    // Sort selector
    document.getElementById('sort-select').addEventListener('change', function() {
        AppState.currentSort = this.value;
        loadAccounts();  // Reload with new sort
    });
    
    // Show archived checkbox
    document.getElementById('show-archived-check').addEventListener('change', function() {
        loadAccounts();  // Reload with/without archived accounts
    });
    
    // Asset period selector
    document.getElementById('asset-period-select').addEventListener('change', function() {
        AppState.currentAssetPeriod = this.value;
        // Reload asset details with new period
        if (AppState.selectedAssetId) {
            loadAssetDetails(AppState.selectedAssetId);
        }
    });
    
    // Initialize modules
    initializeAddAssetModal();
    initializeTagManagement();
    initializeEditTagsModal();
    initializeNoteModal();
    setupModalHandlers();
});

// Expose old global variables for backward compatibility
Object.defineProperty(window, 'chart', {
    get: function() { return AppState.chart; },
    set: function(value) { AppState.chart = value; }
});

Object.defineProperty(window, 'assetChart', {
    get: function() { return AppState.assetChart; },
    set: function(value) { AppState.assetChart = value; }
});

Object.defineProperty(window, 'currentPeriod', {
    get: function() { return AppState.currentPeriod; },
    set: function(value) { AppState.currentPeriod = value; }
});

Object.defineProperty(window, 'currentCurrency', {
    get: function() { return AppState.currentCurrency; },
    set: function(value) { AppState.currentCurrency = value; }
});

Object.defineProperty(window, 'currentAccountType', {
    get: function() { return AppState.currentAccountType; },
    set: function(value) { AppState.currentAccountType = value; }
});

Object.defineProperty(window, 'currentSort', {
    get: function() { return AppState.currentSort; },
    set: function(value) { AppState.currentSort = value; }
});

Object.defineProperty(window, 'accountsData', {
    get: function() { return AppState.accountsData; },
    set: function(value) { AppState.accountsData = value; }
});

Object.defineProperty(window, 'selectedAssetId', {
    get: function() { return AppState.selectedAssetId; },
    set: function(value) { AppState.selectedAssetId = value; }
});

Object.defineProperty(window, 'currentAssetPeriod', {
    get: function() { return AppState.currentAssetPeriod; },
    set: function(value) { AppState.currentAssetPeriod = value; }
});

Object.defineProperty(window, 'currentAssetData', {
    get: function() { return AppState.currentAssetData; },
    set: function(value) { AppState.currentAssetData = value; }
});

// Note: window.currencyData is already a shared reference with AppState.currencyData (set in state.js)

