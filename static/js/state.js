// Global application state
const AppState = {
    chart: null,
    assetChart: null,
    currentPeriod: 'ytd',
    currentCurrency: 'EUR',
    currentAccountType: 'assets',
    currentSort: 'value-desc',
    accountsData: {},
    selectedAssetId: null,
    currentAssetPeriod: 'ytd',
    currentAssetData: null,
    
    // Currency data (initialized in base.html, shared reference)
    currencyData: window.currencyData || {
        list: [],
        symbols: {},
        decimals: {},
        loaded: false
    }
};

// Ensure window.currencyData points to the same object
if (!window.currencyData) {
    window.currencyData = AppState.currencyData;
} else {
    AppState.currencyData = window.currencyData;
}

// Expose globally for backward compatibility
window.AppState = AppState;
