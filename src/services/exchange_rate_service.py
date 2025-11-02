"""
Exchange rate service for fetching and caching USD-based exchange rates.
All rates are stored with USD as base. Conversions between currencies are calculated.
"""
from typing import Optional, Dict


class ExchangeRateService:
    """Service for managing USD-based exchange rate operations."""
    
    def __init__(self, db, exchange_rate_repo):
        """Initialize service with database interface and repository."""
        self.db = db
        self.exchange_rate_repo = exchange_rate_repo
    
    def get_usd_rates(self):
        """
        Get all USD-based exchange rates from cache or API.
        This method is called once per 24 hours max for the entire application.
        Returns dict of {currency_code: rate_vs_usd} or None if unavailable.
        """
        # Try to get from database first (with 24hr cache)
        cached_rates = self.exchange_rate_repo.get_all_rates_usd()
        if cached_rates:
            return cached_rates
        
        # Rates are stale or don't exist, fetch from API
        try:
            import requests
            from concurrent.futures import ThreadPoolExecutor
            from src.config.api_config import (
                get_exchange_rate_api_url, 
                get_exchange_rate_api_timeout,
                get_crypto_price_api_full_url,
                get_crypto_price_api_timeout
            )
            from src.config.currency_metadata import CRYPTO_API_MAPPING
            
            api_rates = {}
            
            def fetch_fiat_rates():
                """Fetch fiat currency rates (USD-based)."""
                response = requests.get(
                    get_exchange_rate_api_url(), 
                    timeout=get_exchange_rate_api_timeout()
                )
                if response.status_code == 200:
                    return response.json().get('rates', {})
                return None
            
            def fetch_crypto_rates():
                """Fetch crypto currency rates."""
                try:
                    response = requests.get(
                        get_crypto_price_api_full_url(),
                        timeout=get_crypto_price_api_timeout()
                    )
                    if response.status_code == 200:
                        crypto_data = response.json()
                        crypto_rates = {}
                        for api_name, currency_code in CRYPTO_API_MAPPING.items():
                            if api_name in crypto_data:
                                crypto_rates[currency_code] = 1.0 / crypto_data[api_name]['usd']
                        return crypto_rates
                except:
                    pass
                return {}
            
            # Fetch both APIs in parallel for speed
            with ThreadPoolExecutor(max_workers=2) as executor:
                fiat_future = executor.submit(fetch_fiat_rates)
                crypto_future = executor.submit(fetch_crypto_rates)
                
                # Get fiat rates (required)
                api_rates = fiat_future.result()
                if not api_rates:
                    return None
                
                # Get crypto rates (optional)
                crypto_rates = crypto_future.result()
                if crypto_rates:
                    api_rates.update(crypto_rates)
            
            # Save USD-based rates to database
            self.exchange_rate_repo.save_rates_bulk_usd(api_rates)
            return api_rates
            
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return None
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another using USD as intermediate.
        Formula: amount_usd = amount / rate_from, amount_to = amount_usd * rate_to
        Returns None if conversion not possible (currency not found).
        """
        if from_currency == to_currency:
            return amount
        
        # Get USD-based rates
        usd_rates = self.get_usd_rates()
        if not usd_rates:
            return None
        
        # Check if both currencies exist
        if from_currency != 'USD' and from_currency not in usd_rates:
            return None
        if to_currency != 'USD' and to_currency not in usd_rates:
            return None
        
        # Convert to USD first
        if from_currency == 'USD':
            amount_in_usd = amount
        else:
            rate_from = usd_rates[from_currency]
            amount_in_usd = amount / rate_from
        
        # Convert from USD to target currency
        if to_currency == 'USD':
            return amount_in_usd
        else:
            rate_to = usd_rates[to_currency]
            return amount_in_usd * rate_to
    
    def convert_with_cached_rates(self, amount: float, from_currency: str, to_currency: str, usd_rates: Dict[str, float]) -> Optional[float]:
        """
        Convert amount using pre-fetched USD rates (for performance in loops).
        Use this when you have already fetched rates and need to do multiple conversions.
        Formula: amount_usd = amount / rate_from, amount_to = amount_usd * rate_to
        """
        if from_currency == to_currency:
            return float(amount)
        
        # Check if both currencies exist
        if from_currency != 'USD' and from_currency not in usd_rates:
            return None
        if to_currency != 'USD' and to_currency not in usd_rates:
            return None
        
        # Convert to USD first
        if from_currency == 'USD':
            amount_in_usd = float(amount)
        else:
            rate_from = usd_rates[from_currency]
            amount_in_usd = float(amount) / rate_from
        
        # Convert from USD to target currency
        if to_currency == 'USD':
            return amount_in_usd
        else:
            rate_to = usd_rates[to_currency]
            return amount_in_usd * rate_to
