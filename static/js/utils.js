// Utility functions

// Format currency according to locale and currency code
function formatCurrency(value, currencyCode = 'EUR', compact = false) {
    if (typeof value !== 'number') {
        value = parseFloat(value);
    }
    if (isNaN(value)) return 'N/A';
    
    // Find currency data
    const currency = AppState.currencyData.list.find(c => c.code === currencyCode) || 
                    AppState.currencyData.list.find(c => c.code === 'EUR'); // fallback to EUR
    
    const options = {
        style: 'currency',
        currency: currency.code,
        minimumFractionDigits: compact ? 0 : 2,
        maximumFractionDigits: compact ? 1 : 2
    };
    
    // Use compact notation for large numbers
    if (compact) {
        options.notation = 'compact';
        options.compactDisplay = 'short';
    }
    
    const formatter = new Intl.NumberFormat(currency.locale, options);
    
    return formatter.format(value);
}

// Format large numbers with K, M, B suffixes - maximum 5 digits including decimal point
function formatCompactNumber(value, currencyCode = 'EUR') {
    if (typeof value !== 'number') {
        value = parseFloat(value);
    }
    if (isNaN(value)) return 'N/A';
    
    const absValue = Math.abs(value);
    const currency = AppState.currencyData.list.find(c => c.code === currencyCode) || 
                    AppState.currencyData.list.find(c => c.code === 'EUR');
    const symbol = currency.symbol;
    
    let formattedValue;
    
    if (absValue >= 1000000000) {
        // Billions: max 5 digits including decimal (e.g., 123.4B, 12.34B, 1.234B)
        const billions = value / 1000000000;
        if (absValue >= 100000000000) {
            formattedValue = Math.round(billions) + 'B';  // 123B
        } else if (absValue >= 10000000000) {
            formattedValue = billions.toFixed(1) + 'B';   // 12.3B
        } else {
            formattedValue = billions.toFixed(2) + 'B';   // 1.23B
        }
    } else if (absValue >= 1000000) {
        // Millions: max 5 digits including decimal (e.g., 123.4M, 12.34M, 1.234M)
        const millions = value / 1000000;
        if (absValue >= 100000000) {
            formattedValue = Math.round(millions) + 'M';  // 123M
        } else if (absValue >= 10000000) {
            formattedValue = millions.toFixed(1) + 'M';   // 12.3M
        } else {
            formattedValue = millions.toFixed(2) + 'M';   // 1.23M
        }
    } else if (absValue >= 1000) {
        // Thousands: max 5 digits including decimal (e.g., 123.4K, 12.34K, 1.234K)
        const thousands = value / 1000;
        if (absValue >= 100000) {
            formattedValue = Math.round(thousands) + 'K'; // 123K
        } else if (absValue >= 10000) {
            formattedValue = thousands.toFixed(1) + 'K';  // 12.3K
        } else {
            formattedValue = thousands.toFixed(2) + 'K';  // 1.23K
        }
    } else {
        // Less than 1K - show with decimals (max 5 digits including decimal point)
        if (absValue >= 100) {
            // 100-999: show with 2 decimals (e.g., 234.54)
            formattedValue = value.toFixed(2);
        } else if (absValue >= 10) {
            // 10-99: show with 2 decimals (e.g., 12.34)
            formattedValue = value.toFixed(2);
        } else if (absValue >= 1) {
            // 1-9: show with 2 decimals (e.g., 3.08)
            formattedValue = value.toFixed(2);
        } else if (absValue > 0) {
            // 0.01-0.99: show with up to 4 decimals (e.g., 0.0894)
            formattedValue = value.toFixed(4);
        } else {
            formattedValue = '0';
        }
        // Remove trailing zeros and unnecessary decimal point
        formattedValue = parseFloat(formattedValue).toString();
    }
    
    // Add currency symbol (handle different positions based on locale)
    if (currencyCode === 'USD' || currencyCode === 'GBP' || currencyCode === 'INR') {
        return symbol + formattedValue;
    } else {
        return formattedValue + ' ' + symbol;
    }
}

// Show success toast notification
function showSuccessToast(message) {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-check-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    showToast(toastHTML);
}

// Show error toast notification
function showErrorToast(message) {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-danger border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    showToast(toastHTML);
}

// Generic toast display function
function showToast(toastHTML) {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Expose functions globally
window.formatCurrency = formatCurrency;
window.formatCompactNumber = formatCompactNumber;
window.showSuccessToast = showSuccessToast;
window.showErrorToast = showErrorToast;
window.showToast = showToast;
