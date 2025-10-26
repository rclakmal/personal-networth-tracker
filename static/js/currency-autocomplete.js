/**
 * Currency autocomplete/search functionality
 */

function initializeCurrencyAutocomplete() {
    const currencySearch = document.getElementById('currency-search');
    const currencySelector = document.getElementById('currency-selector');
    const currencyDropdown = document.getElementById('currency-dropdown');
    
    if (!currencySearch || !currencySelector || !currencyDropdown) {
        console.error('Currency elements not found');
        return;
    }
    
    let allCurrencies = [];
    // Prioritize session currency over localStorage (session is user-specific, localStorage is browser-wide)
    let selectedCurrency = (window.sessionData && window.sessionData.currency) || 
                          localStorage.getItem('networth-currency') || 
                          'EUR';
    
    // Fetch currencies from API
    fetch('/api/currencies')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Store currency metadata globally
            window.currencyData.list = data.all || [];
            data.all.forEach(currency => {
                window.currencyData.symbols[currency.code] = currency.symbol;
                window.currencyData.decimals[currency.code] = currency.decimals || 2;
            });
            window.currencyData.loaded = true;
            
            // Sync with AppState if it exists
            if (window.AppState && window.AppState.currencyData) {
                window.AppState.currencyData = window.currencyData;
            }
            
            // Store all currencies with type info
            allCurrencies = [
                ...(data.fiat || []).map(c => ({...c, group: '💵 Fiat Currencies'})),
                ...(data.crypto || []).map(c => ({...c, group: '🪙 Cryptocurrencies'}))
            ];
            
            // Set initial value
            const initialCurrency = allCurrencies.find(c => c.code === selectedCurrency);
            if (initialCurrency) {
                currencySearch.value = `${initialCurrency.code} (${initialCurrency.symbol}) - ${initialCurrency.name}`;
                currencySelector.value = initialCurrency.code;
            }
            
            // Function to filter and display currencies
            function filterCurrencies(searchTerm) {
                const term = searchTerm.toLowerCase();
                
                // If empty search, show all currencies
                let filtered;
                if (!term || term.length === 0) {
                    filtered = allCurrencies;
                } else {
                    filtered = allCurrencies.filter(currency => 
                        currency.code.toLowerCase().includes(term) ||
                        currency.name.toLowerCase().includes(term) ||
                        currency.symbol.toLowerCase().includes(term)
                    );
                }
                
                if (filtered.length === 0) {
                    currencyDropdown.innerHTML = '<div class="currency-no-results" style="padding: 8px; text-align: center;">No currencies found</div>';
                    currencyDropdown.style.display = 'block';
                    return;
                }
                
                // Group by type
                const fiat = filtered.filter(c => c.type === 'fiat');
                const crypto = filtered.filter(c => c.type === 'crypto');
                
                let html = '';
                
                if (fiat.length > 0) {
                    html += '<div class="currency-group-header" style="padding: 6px 12px; font-weight: 600; font-size: 0.85rem; position: sticky; top: 0;">💵 Fiat Currencies</div>';
                    fiat.forEach(currency => {
                        html += `
                            <div class="currency-option" data-code="${currency.code}" style="padding: 8px 12px; cursor: pointer; font-size: 0.9rem;">
                                <strong>${currency.code}</strong> (${currency.symbol}) - ${currency.name}
                            </div>
                        `;
                    });
                }
                
                if (crypto.length > 0) {
                    html += '<div class="currency-group-header" style="padding: 6px 12px; font-weight: 600; font-size: 0.85rem; position: sticky; top: 0;">🪙 Cryptocurrencies</div>';
                    crypto.forEach(currency => {
                        html += `
                            <div class="currency-option" data-code="${currency.code}" style="padding: 8px 12px; cursor: pointer; font-size: 0.9rem;">
                                <strong>${currency.code}</strong> (${currency.symbol}) - ${currency.name}
                            </div>
                        `;
                    });
                }
                
                currencyDropdown.innerHTML = html;
                currencyDropdown.style.display = 'block';
                
                // Add click handlers
                document.querySelectorAll('.currency-option').forEach(option => {
                    option.addEventListener('click', function() {
                        const code = this.dataset.code;
                        const currency = allCurrencies.find(c => c.code === code);
                        
                        if (currency) {
                            currencySearch.value = `${currency.code} (${currency.symbol}) - ${currency.name}`;
                            currencySelector.value = currency.code;
                            currencyDropdown.style.display = 'none';
                            
                            // Save preference
                            localStorage.setItem('networth-currency', currency.code);
                            
                            // Save to server
                            fetch('/api/user/currency', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': window.sessionData.csrfToken
                                },
                                body: JSON.stringify({ currency: currency.code })
                            }).then(() => {
                                // Reload page to apply new currency
                                window.location.reload();
                            }).catch(err => console.error('Failed to save currency:', err));
                        }
                    });
                });
            }
            
            // Event listeners
            currencySearch.addEventListener('focus', function() {
                // Show all currencies when focused if empty
                if (!this.value || this.value.length === 0) {
                    filterCurrencies('');
                } else {
                    // Extract the search term from the current value
                    const currentCode = currencySelector.value;
                    const currentCurrency = allCurrencies.find(c => c.code === currentCode);
                    if (currentCurrency) {
                        // Clear to allow searching
                        this.value = '';
                        filterCurrencies('');
                    }
                }
            });
            
            currencySearch.addEventListener('input', function() {
                filterCurrencies(this.value);
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(e) {
                if (!currencySearch.contains(e.target) && !currencyDropdown.contains(e.target)) {
                    currencyDropdown.style.display = 'none';
                    
                    // Restore selected currency display if user clicked away
                    const currentCode = currencySelector.value;
                    const currentCurrency = allCurrencies.find(c => c.code === currentCode);
                    if (currentCurrency && currencySearch.value !== `${currentCurrency.code} (${currentCurrency.symbol}) - ${currentCurrency.name}`) {
                        currencySearch.value = `${currentCurrency.code} (${currentCurrency.symbol}) - ${currentCurrency.name}`;
                    }
                }
            });
            
            // Trigger currency loaded event
            if (typeof window.onCurrenciesLoaded === 'function') {
                window.onCurrenciesLoaded();
            }
        })
        .catch(error => {
            console.error('Error loading currencies:', error);
            currencySearch.placeholder = 'Failed to load currencies';
            currencySearch.disabled = true;
        });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(initializeCurrencyAutocomplete, 100);
    });
} else {
    setTimeout(initializeCurrencyAutocomplete, 100);
}
