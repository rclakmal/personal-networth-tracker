"""
Fallback data for when external APIs are unavailable.
This file contains static fallback values used when the application cannot reach external services.
"""

# Fallback exchange rates (EUR as base)
# These rates are approximate and should be updated periodically
# The application will always try to fetch live rates from the API first
FALLBACK_EXCHANGE_RATES = {
    'EUR': 1.0,
    'USD': 1.0535,
    'GBP': 0.8522,
    'JPY': 161.62,
    'CHF': 0.9359,
    'CAD': 1.4726,
    'AUD': 1.6232,
    'CNY': 7.6438,
    'INR': 88.45,
    'BRL': 6.12,
}

# Fallback currency list
# Used when the currency API is unavailable
FALLBACK_FIAT_CURRENCIES = [
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'type': 'fiat'},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'type': 'fiat'},
    {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'type': 'fiat'},
    {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥', 'type': 'fiat'},
    {'code': 'CHF', 'name': 'Swiss Franc', 'symbol': 'Fr', 'type': 'fiat'},
    {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': '$', 'type': 'fiat'},
    {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': '$', 'type': 'fiat'},
    {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥', 'type': 'fiat'},
    {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹', 'type': 'fiat'},
    {'code': 'BRL', 'name': 'Brazilian Real', 'symbol': 'R$', 'type': 'fiat'},
]

FALLBACK_CRYPTO_CURRENCIES = [
    {'code': 'BTC', 'name': 'Bitcoin', 'symbol': '₿', 'type': 'crypto'},
    {'code': 'ETH', 'name': 'Ethereum', 'symbol': 'Ξ', 'type': 'crypto'},
]

# Extended crypto list (used when API is available but doesn't include crypto)
EXTENDED_CRYPTO_CURRENCIES = [
    {'code': 'BTC', 'name': 'Bitcoin', 'symbol': '₿', 'type': 'crypto'},
    {'code': 'ETH', 'name': 'Ethereum', 'symbol': 'Ξ', 'type': 'crypto'},
    {'code': 'USDT', 'name': 'Tether', 'symbol': '₮', 'type': 'crypto'},
    {'code': 'USDC', 'name': 'USD Coin', 'symbol': 'USDC', 'type': 'crypto'},
    {'code': 'BNB', 'name': 'Binance Coin', 'symbol': 'BNB', 'type': 'crypto'},
    {'code': 'XRP', 'name': 'Ripple', 'symbol': 'XRP', 'type': 'crypto'},
    {'code': 'ADA', 'name': 'Cardano', 'symbol': 'ADA', 'type': 'crypto'},
    {'code': 'SOL', 'name': 'Solana', 'symbol': 'SOL', 'type': 'crypto'},
    {'code': 'DOGE', 'name': 'Dogecoin', 'symbol': 'Ð', 'type': 'crypto'},
    {'code': 'DOT', 'name': 'Polkadot', 'symbol': 'DOT', 'type': 'crypto'},
    {'code': 'MATIC', 'name': 'Polygon', 'symbol': 'MATIC', 'type': 'crypto'},
    {'code': 'LTC', 'name': 'Litecoin', 'symbol': 'Ł', 'type': 'crypto'},
]

