"""
Networth service for business logic operations.
Service layer contains all business logic: date calculations, aggregations, currency conversions.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, date
from decimal import Decimal
from src.repositories.account_repository import AccountRepository
from src.repositories.account_history_repository import AccountHistoryRepository
from src.repositories.tag_repository import TagRepository
from src.services.exchange_rate_service import ExchangeRateService


class NetworthService:
    """Service class for Networth calculation and analysis business logic."""
    
    def __init__(self, account_repository: AccountRepository, history_repository: AccountHistoryRepository, 
                 tag_repository: TagRepository, exchange_rate_service: ExchangeRateService):
        """Initialize service with repositories."""
        self.account_repository = account_repository
        self.history_repository = history_repository
        self.tag_repository = tag_repository
        self.exchange_rate_service = exchange_rate_service
    
    def calculate_networth_for_period(self, user_id: int, period: str, target_currency: str) -> Dict[str, Any]:
        """
        Calculate networth data for a specific period.
        Business logic: date range calculation, data aggregation, currency conversion.
        """
        # Calculate date range based on period
        end_date = datetime.now().date()
        start_date = self._calculate_start_date(period, end_date, user_id)
        
        if start_date is None:
            return {'error': 'Invalid period'}
        
        # Get USD-based exchange rates once for the entire request (cached for performance)
        usd_rates = self.exchange_rate_service.get_usd_rates()
        if not usd_rates:
            return {'error': 'Exchange rates unavailable'}
        
        # Get all accounts with their latest values
        accounts = self.account_repository.find_with_latest_value_by_user_id(user_id)
        
        # Get historical data within the period
        history = self.history_repository.find_by_user_and_date_range(user_id, start_date, end_date)
        
        # Get the most recent value BEFORE the period starts for each account (to initialize carry-forward)
        history_before = self.history_repository.find_last_before_date_by_user(user_id, start_date)
        
        # Build timeline and calculate networth for each date
        networth_data = self._build_networth_timeline(
            accounts, history, history_before, start_date, end_date, target_currency, usd_rates
        )
        
        return networth_data
    
    def _calculate_start_date(self, period: str, end_date: date, user_id: int) -> date:
        """Calculate start date based on period string."""
        if period == 'week':
            return end_date - timedelta(days=7)
        elif period == 'month':
            return end_date - timedelta(days=30)
        elif period == '3months':
            return end_date - timedelta(days=90)
        elif period == '6months':
            return end_date - timedelta(days=180)
        elif period == 'ytd':
            return datetime(end_date.year, 1, 1).date()
        elif period in ['year', '1y']:
            return end_date - timedelta(days=365)
        elif period == '2years':
            return end_date.replace(year=end_date.year - 2)
        elif period in ['3years', '3y']:
            return end_date.replace(year=end_date.year - 3)
        elif period == '4years':
            return end_date.replace(year=end_date.year - 4)
        elif period in ['5years', '5y']:
            return end_date.replace(year=end_date.year - 5)
        elif period in ['max', 'all']:
            # All time - get the earliest date from history
            earliest = self.history_repository.find_earliest_date_for_user(user_id)
            if earliest:
                return earliest
            else:
                # No history data, use a reasonable default
                return end_date.replace(year=end_date.year - 1)
        else:
            return None
    
    def _build_networth_timeline(self, accounts: List[dict], history: List[dict], 
                                  history_before: List[dict], start_date: date, end_date: date,
                                  target_currency: str, usd_rates: dict) -> Dict[str, Any]:
        """
        Build a timeline of networth values for each date in the range.
        Business logic: carry-forward values, currency conversion, asset/liability classification.
        """
        # Build a timeline of values for each account
        account_timeline = {}
        
        # Initialize with values from before the period
        for record in history_before:
            account_id = record['account_id']
            account_timeline[account_id] = {
                'currency': record['currency'],
                'archived': False,  # Will be updated if we have data in the period
                'values': {}
            }
        
        # Add values within the period
        for record in history:
            account_id = record['account_id']
            date_str = record['date']
            
            if account_id not in account_timeline:
                account_timeline[account_id] = {
                    'currency': record['currency'],
                    'archived': record['archived'],
                    'values': {}
                }
            
            # Store value for this date (later entries will overwrite earlier ones on same date)
            account_timeline[account_id]['values'][date_str] = record['value']
            account_timeline[account_id]['currency'] = record['currency']
            account_timeline[account_id]['archived'] = record['archived']
        
        # Generate ALL dates in the period range for smooth charts
        current_date = start_date
        all_dates_in_range = []
        while current_date <= end_date:
            all_dates_in_range.append(current_date.isoformat())
            current_date += timedelta(days=1)
        
        # Calculate networth for each date by summing all accounts with their last known value
        networth_by_date = {}
        
        # Track last known value for each account (for carrying forward)
        # Initialize with values from BEFORE the period
        account_last_values = {}
        for record in history_before:
            account_id = record['account_id']
            account_last_values[account_id] = {
                'value': record['value'],
                'currency': record['currency']
            }
        
        for date_str in all_dates_in_range:
            networth_by_date[date_str] = {
                'date': date_str,
                'total': Decimal('0'),
                'assets': Decimal('0'),
                'liabilities': Decimal('0')
            }
            
            # For each account, update its last known value if there's a new entry for this date
            for account_id, account_data in account_timeline.items():
                # Check if there's a new value for this date
                if date_str in account_data['values']:
                    account_last_values[account_id] = {
                        'value': account_data['values'][date_str],
                        'currency': account_data['currency']
                    }
                
                # Use the last known value (carried forward)
                if account_id in account_last_values:
                    last_value = account_last_values[account_id]['value']
                    currency = account_last_values[account_id]['currency']
                    
                    # Convert to target currency using cached USD rates
                    value_in_target = self.exchange_rate_service.convert_with_cached_rates(
                        last_value,
                        currency,
                        target_currency,
                        usd_rates
                    )
                    
                    # Skip if conversion failed (currency not available)
                    if value_in_target is None:
                        continue
                    
                    # Include all historical values regardless of current archived status
                    # Historical data represents actual networth at that time
                    networth_by_date[date_str]['total'] += Decimal(str(value_in_target))
                    
                    if value_in_target >= 0:
                        networth_by_date[date_str]['assets'] += Decimal(str(value_in_target))
                    else:
                        networth_by_date[date_str]['liabilities'] += Decimal(str(value_in_target))
        
        # Convert to list and sort by date
        dates = []
        net_worth = []
        assets_data = []
        liabilities_data = []
        
        for date_str in sorted(networth_by_date.keys()):
            data = networth_by_date[date_str]
            dates.append(date_str)
            net_worth.append(float(data['total']))
            assets_data.append(float(data['assets']))
            liabilities_data.append(float(data['liabilities']))
        
        return {
            'dates': dates,
            'net_worth': net_worth,
            'assets': assets_data,
            'liabilities': liabilities_data
        }
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags used by users."""
        return self.tag_repository.find_all()
    
    def get_currency_list(self) -> Dict[str, Any]:
        """
        Get list of available currencies.
        Business logic: check cache freshness, fetch from API if needed, build response structure.
        """
        from src.config.currency_metadata import (
            EXTENDED_CRYPTO_CURRENCIES, 
            CURRENCY_NAMES, 
            CURRENCY_SYMBOLS,
            COMMON_CURRENCY_CODES
        )
        
        # Fetch rates (will use cache if fresh)
        rates = self.exchange_rate_service.get_usd_rates()
        
        if rates:
            # Build fiat currency list from API response
            fiat_currencies = []
            crypto_codes = set([crypto['code'] for crypto in EXTENDED_CRYPTO_CURRENCIES])
            
            for code in sorted(rates.keys()):
                # Skip crypto codes (they're handled separately)
                if code not in crypto_codes:
                    fiat_currencies.append({
                        'code': code,
                        'name': CURRENCY_NAMES.get(code, code),
                        'symbol': CURRENCY_SYMBOLS.get(code, code),
                        'type': 'fiat'
                    })
            
            # Combine all currencies
            all_currencies = fiat_currencies + EXTENDED_CRYPTO_CURRENCIES
            
            # Common currencies
            common_currencies = [c for c in fiat_currencies if c['code'] in COMMON_CURRENCY_CODES]
            
            result = {
                'all': all_currencies,
                'fiat': fiat_currencies,
                'crypto': EXTENDED_CRYPTO_CURRENCIES,
                'common': common_currencies,
                'loaded': True
            }
            
            return result
        else:
            # API failed
            return {
                'error': 'Currency API unavailable. Please check your internet connection or API configuration.',
                'loaded': False
            }
    
    def get_exchange_rates_for_base(self, base_currency: str) -> Dict[str, Any]:
        """
        Get exchange rates for a base currency.
        Business logic: rate conversion from USD-based to requested base.
        """
        # Get USD-based rates
        usd_rates = self.exchange_rate_service.get_usd_rates()
        
        if usd_rates is None:
            return {
                'error': 'Exchange rate API unavailable. Please check your internet connection or API configuration.',
                'loaded': False
            }
        
        # If base is USD, return as-is
        if base_currency == 'USD':
            return usd_rates
        
        # Convert all rates to requested base currency
        if base_currency not in usd_rates:
            return {
                'error': f'Base currency {base_currency} not found in exchange rates',
                'loaded': False
            }
        
        base_rate = usd_rates[base_currency]
        converted_rates = {}
        for currency, rate in usd_rates.items():
            # Convert: rate_vs_usd to rate_vs_base
            # If EUR rate is 0.9 (1 USD = 0.9 EUR) and we want GBP vs EUR:
            # GBP rate is 0.8 (1 USD = 0.8 GBP)
            # 1 EUR = 1/0.9 USD = 1.111 USD
            # 1 EUR = 1.111 * 0.8 = 0.889 GBP
            converted_rates[currency] = rate / base_rate
        
        return converted_rates
