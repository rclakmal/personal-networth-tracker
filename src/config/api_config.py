"""
API configuration loader.
Loads API endpoints and settings from api_config.json
"""
import json
import os

def load_api_config():
    """Load API configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), 'api_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

# Load config on module import
API_CONFIG = load_api_config()

# Helper functions for easy access
def get_exchange_rate_api_url():
    """Get exchange rate API URL."""
    return API_CONFIG['exchange_rate_api']['url']

def get_exchange_rate_api_timeout():
    """Get exchange rate API timeout."""
    return API_CONFIG['exchange_rate_api']['timeout']

def get_crypto_price_api_url():
    """Get crypto price API URL."""
    return API_CONFIG['crypto_price_api']['url']

def get_crypto_price_api_params():
    """Get crypto price API parameters."""
    return API_CONFIG['crypto_price_api']['params']

def get_crypto_price_api_timeout():
    """Get crypto price API timeout."""
    return API_CONFIG['crypto_price_api']['timeout']

def get_crypto_price_api_full_url():
    """Get full crypto price API URL with parameters."""
    url = get_crypto_price_api_url()
    params = get_crypto_price_api_params()
    param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{url}?{param_str}"
