"""
Networth controller for handling networth and chart-related API endpoints.
"""
from flask import request, jsonify, session
from datetime import datetime, timedelta
from decimal import Decimal


class NetworthController:
    """Controller for networth-related operations."""
    
    def __init__(self, db, account_repository):
        """Initialize controller with database interface and account repository."""
        self.db = db
        self.account_repository = account_repository
    
    def _get_current_user_id(self):
        """Get current user ID from session."""
        return session.get('user_id')
    
    def _require_authentication(self):
        """Check if user is authenticated."""
        user_id = self._get_current_user_id()
        if not user_id:
            return None, jsonify({'error': 'Authentication required'}), 401
        return user_id, None, None
    
    def get_networth(self, period):
        """Get networth data for a specific period."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        target_currency = request.args.get('currency', session.get('currency', 'EUR'))
        
        # Calculate date range based on period
        end_date = datetime.now().date()
        
        if period == 'week':
            # Last 7 days
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            # Last 30 days
            start_date = end_date - timedelta(days=30)
        elif period == '3months':
            # Last 3 months
            start_date = end_date - timedelta(days=90)
        elif period == '6months':
            # Last 6 months
            start_date = end_date - timedelta(days=180)
        elif period == 'ytd':
            # Year to date
            start_date = datetime(end_date.year, 1, 1).date()
        elif period == 'year' or period == '1y':
            # Last 12 months
            start_date = end_date - timedelta(days=365)
        elif period == '2years':
            # Last 2 years
            start_date = end_date.replace(year=end_date.year - 2)
        elif period == '3years' or period == '3y':
            # Last 3 years
            start_date = end_date.replace(year=end_date.year - 3)
        elif period == '4years':
            # Last 4 years
            start_date = end_date.replace(year=end_date.year - 4)
        elif period == '5years' or period == '5y':
            # Last 5 years
            start_date = end_date.replace(year=end_date.year - 5)
        elif period == 'max' or period == 'all':
            # All time - get the earliest date from history
            earliest_query = '''
            SELECT MIN(DATE(recorded_date)) as earliest_date
            FROM account_history ah
            INNER JOIN accounts a ON ah.account_id = a.id
            WHERE a.user_id = ?
            '''
            earliest_result = self.db.execute_query(earliest_query, (user_id,))
            if earliest_result and earliest_result[0]['earliest_date']:
                start_date = datetime.strptime(earliest_result[0]['earliest_date'], '%Y-%m-%d').date()
            else:
                # No history data, use a reasonable default
                start_date = end_date.replace(year=end_date.year - 1)
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Fetch exchange rates
        exchange_rates = self._fetch_exchange_rates(target_currency)
        
        # Get all active accounts for the user
        query = '''
        SELECT a.id, a.name, a.currency, a.current_value, a.archived,
               COALESCE(
                   (SELECT value 
                    FROM account_history ah 
                    WHERE ah.account_id = a.id 
                    ORDER BY ah.recorded_date DESC 
                    LIMIT 1), 
                   a.current_value
               ) as latest_value
        FROM accounts a
        WHERE a.user_id = ?
        '''
        accounts = self.db.execute_query(query, (user_id,))
        
        # Get historical data within the period
        query = '''
        SELECT DATE(ah.recorded_date) as date, ah.account_id, ah.value, a.currency, a.archived
        FROM account_history ah
        INNER JOIN accounts a ON ah.account_id = a.id
        WHERE a.user_id = ? AND DATE(ah.recorded_date) >= ? AND DATE(ah.recorded_date) <= ?
        ORDER BY ah.account_id, ah.recorded_date ASC
        '''
        history = self.db.execute_query(query, (user_id, start_date, end_date))
        
        # Get the most recent value BEFORE the period starts for each account (to initialize carry-forward)
        query_before = '''
        SELECT ah.account_id, ah.value, a.currency, MAX(DATE(ah.recorded_date)) as last_date
        FROM account_history ah
        INNER JOIN accounts a ON ah.account_id = a.id
        WHERE a.user_id = ? AND DATE(ah.recorded_date) < ?
        GROUP BY ah.account_id
        '''
        history_before = self.db.execute_query(query_before, (user_id, start_date))
        
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
            date = record['date']
            
            if account_id not in account_timeline:
                account_timeline[account_id] = {
                    'currency': record['currency'],
                    'archived': record['archived'],
                    'values': {}
                }
            
            # Store value for this date (later entries will overwrite earlier ones on same date)
            account_timeline[account_id]['values'][date] = record['value']
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
                    
                    # Convert to target currency
                    value_in_target = self._convert_currency(
                        last_value,
                        currency,
                        target_currency,
                        exchange_rates
                    )
                    
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
        
        return jsonify({
            'dates': dates,
            'net_worth': net_worth,
            'assets': assets_data,
            'liabilities': liabilities_data
        })
    
    def get_tags(self):
        """Get all unique tags used by the current user."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Use repository method to get all unique tags from tags table
        tags = self.account_repository.get_all_tags()
        
        return jsonify({'tags': tags})
    
    def get_currencies(self):
        """Get list of available currencies from exchange rate API."""
        try:
            # Fetch from exchangerate-api.com (free tier, no API key required)
            import requests
            response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Comprehensive currency names mapping
                currency_names = {
                    # Major currencies
                    'USD': 'US Dollar', 'EUR': 'Euro', 'GBP': 'British Pound', 'JPY': 'Japanese Yen',
                    'CHF': 'Swiss Franc', 'CAD': 'Canadian Dollar', 'AUD': 'Australian Dollar',
                    'CNY': 'Chinese Yuan', 'INR': 'Indian Rupee', 'BRL': 'Brazilian Real',
                    'NZD': 'New Zealand Dollar', 'SEK': 'Swedish Krona', 'NOK': 'Norwegian Krone',
                    'DKK': 'Danish Krone', 'KRW': 'South Korean Won', 'SGD': 'Singapore Dollar',
                    'HKD': 'Hong Kong Dollar', 'MXN': 'Mexican Peso', 'ZAR': 'South African Rand',
                    'RUB': 'Russian Ruble', 'TRY': 'Turkish Lira', 'PLN': 'Polish Zloty',
                    'THB': 'Thai Baht', 'IDR': 'Indonesian Rupiah', 'MYR': 'Malaysian Ringgit',
                    'PHP': 'Philippine Peso', 'CZK': 'Czech Koruna', 'HUF': 'Hungarian Forint',
                    'ILS': 'Israeli Shekel', 'AED': 'UAE Dirham', 'SAR': 'Saudi Riyal',
                    'ARS': 'Argentine Peso', 'CLP': 'Chilean Peso', 'COP': 'Colombian Peso',
                    'PEN': 'Peruvian Sol', 'EGP': 'Egyptian Pound', 'KES': 'Kenyan Shilling',
                    'NGN': 'Nigerian Naira', 'PKR': 'Pakistani Rupee', 'BDT': 'Bangladeshi Taka',
                    'VND': 'Vietnamese Dong', 'UAH': 'Ukrainian Hryvnia', 'RON': 'Romanian Leu',
                    'BGN': 'Bulgarian Lev', 'HRK': 'Croatian Kuna', 'ISK': 'Icelandic Krona',
                    # Additional currencies from API
                    'LKR': 'Sri Lankan Rupee', 'NPR': 'Nepalese Rupee', 'MMK': 'Myanmar Kyat',
                    'LAK': 'Lao Kip', 'KHR': 'Cambodian Riel', 'BND': 'Brunei Dollar',
                    'TWD': 'Taiwan Dollar', 'KZT': 'Kazakhstani Tenge', 'UZS': 'Uzbekistani Som',
                    'GEL': 'Georgian Lari', 'AMD': 'Armenian Dram', 'AZN': 'Azerbaijani Manat',
                    'BYN': 'Belarusian Ruble', 'MDL': 'Moldovan Leu', 'RSD': 'Serbian Dinar',
                    'MKD': 'Macedonian Denar', 'ALL': 'Albanian Lek', 'BAM': 'Bosnia-Herzegovina Mark',
                    'TND': 'Tunisian Dinar', 'DZD': 'Algerian Dinar', 'MAD': 'Moroccan Dirham',
                    'LYD': 'Libyan Dinar', 'ETB': 'Ethiopian Birr', 'UGX': 'Ugandan Shilling',
                    'TZS': 'Tanzanian Shilling', 'GHS': 'Ghanaian Cedi', 'XOF': 'West African CFA Franc',
                    'XAF': 'Central African CFA Franc', 'MUR': 'Mauritian Rupee', 'MGA': 'Malagasy Ariary',
                    'MWK': 'Malawian Kwacha', 'ZMW': 'Zambian Kwacha', 'BWP': 'Botswana Pula',
                    'NAD': 'Namibian Dollar', 'AOA': 'Angolan Kwanza', 'MZN': 'Mozambican Metical',
                    'JOD': 'Jordanian Dinar', 'KWD': 'Kuwaiti Dinar', 'BHD': 'Bahraini Dinar',
                    'OMR': 'Omani Rial', 'QAR': 'Qatari Riyal', 'IQD': 'Iraqi Dinar',
                    'YER': 'Yemeni Rial', 'LBP': 'Lebanese Pound', 'SYP': 'Syrian Pound',
                    'AFN': 'Afghan Afghani', 'IRR': 'Iranian Rial', 'UYU': 'Uruguayan Peso',
                    'PYG': 'Paraguayan Guarani', 'BOB': 'Bolivian Boliviano', 'VES': 'Venezuelan Bolívar',
                    'GTQ': 'Guatemalan Quetzal', 'HNL': 'Honduran Lempira', 'NIO': 'Nicaraguan Córdoba',
                    'CRC': 'Costa Rican Colón', 'PAB': 'Panamanian Balboa', 'DOP': 'Dominican Peso',
                    'HTG': 'Haitian Gourde', 'JMD': 'Jamaican Dollar', 'TTD': 'Trinidad and Tobago Dollar',
                    'BBD': 'Barbadian Dollar', 'BZD': 'Belize Dollar', 'BSD': 'Bahamian Dollar',
                    'FJD': 'Fijian Dollar', 'PGK': 'Papua New Guinean Kina', 'WST': 'Samoan Tala',
                    'TOP': 'Tongan Paʻanga', 'VUV': 'Vanuatu Vatu', 'SBD': 'Solomon Islands Dollar',
                    'MVR': 'Maldivian Rufiyaa', 'KYD': 'Cayman Islands Dollar', 'BMD': 'Bermudian Dollar',
                    'GIP': 'Gibraltar Pound', 'FKP': 'Falkland Islands Pound', 'SHP': 'Saint Helena Pound',
                    'JEP': 'Jersey Pound', 'GGP': 'Guernsey Pound', 'IMP': 'Isle of Man Pound',
                    'SLL': 'Sierra Leonean Leone', 'GMD': 'Gambian Dalasi', 'GNF': 'Guinean Franc',
                    'LRD': 'Liberian Dollar', 'SDG': 'Sudanese Pound', 'SSP': 'South Sudanese Pound',
                    'ERN': 'Eritrean Nakfa', 'DJF': 'Djiboutian Franc', 'SOS': 'Somali Shilling',
                    'SCR': 'Seychellois Rupee', 'KMF': 'Comorian Franc', 'CVE': 'Cape Verdean Escudo',
                    'STN': 'São Tomé and Príncipe Dobra', 'SZL': 'Swazi Lilangeni', 'LSL': 'Lesotho Loti',
                    'BIF': 'Burundian Franc', 'RWF': 'Rwandan Franc', 'CDF': 'Congolese Franc',
                    'XPF': 'CFP Franc', 'ANG': 'Netherlands Antillean Guilder', 'AWG': 'Aruban Florin',
                    'SRD': 'Surinamese Dollar', 'GYD': 'Guyanese Dollar', 'CUP': 'Cuban Peso',
                    'MNT': 'Mongolian Tögrög', 'BTN': 'Bhutanese Ngultrum', 'TMT': 'Turkmenistani Manat',
                    'TJS': 'Tajikistani Somoni', 'KGS': 'Kyrgyzstani Som',
                }
                
                # Currency symbols mapping
                currency_symbols = {
                    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CHF': 'Fr', 'CAD': '$',
                    'AUD': '$', 'CNY': '¥', 'INR': '₹', 'BRL': 'R$', 'NZD': '$', 'SEK': 'kr',
                    'NOK': 'kr', 'DKK': 'kr', 'KRW': '₩', 'SGD': '$', 'HKD': '$', 'MXN': '$',
                    'ZAR': 'R', 'RUB': '₽', 'TRY': '₺', 'PLN': 'zł', 'THB': '฿', 'IDR': 'Rp',
                    'MYR': 'RM', 'PHP': '₱', 'CZK': 'Kč', 'HUF': 'Ft', 'ILS': '₪', 'AED': 'د.إ',
                    'SAR': '﷼', 'ARS': '$', 'CLP': '$', 'COP': '$', 'PEN': 'S/', 'EGP': '£',
                    'KES': 'KSh', 'NGN': '₦', 'PKR': '₨', 'BDT': '৳', 'VND': '₫', 'UAH': '₴',
                    'RON': 'lei', 'BGN': 'лв', 'HRK': 'kn', 'ISK': 'kr', 'LKR': 'Rs', 'NPR': 'Rs',
                    'MMK': 'K', 'TWD': 'NT$', 'KZT': '₸', 'GEL': '₾', 'AMD': '֏', 'AZN': '₼',
                    'BYN': 'Br', 'RSD': 'din', 'ALL': 'L', 'TND': 'DT', 'DZD': 'DA', 'MAD': 'DH',
                    'JOD': 'JD', 'KWD': 'KD', 'BHD': 'BD', 'OMR': 'OMR', 'QAR': 'QR', 'IQD': 'IQD',
                    'LBP': 'LL', 'UYU': '$U', 'PYG': '₲', 'BOB': 'Bs', 'VES': 'Bs.S', 'GTQ': 'Q',
                    'HNL': 'L', 'NIO': 'C$', 'CRC': '₡', 'DOP': 'RD$', 'JMD': 'J$', 'TTD': 'TT$',
                    'FJD': 'FJ$', 'BWP': 'P', 'NAD': 'N$', 'MUR': '₨', 'MVR': 'Rf', 'SCR': '₨',
                    'LRD': 'L$', 'SRD': '$', 'GYD': 'G$', 'MNT': '₮', 'KGS': 'с',
                }
                
                # Cryptocurrencies (not in standard exchange APIs, add from config)
                from src.config.fallback_data import EXTENDED_CRYPTO_CURRENCIES
                crypto_currencies = EXTENDED_CRYPTO_CURRENCIES
                
                # Build fiat currency list from API response - INCLUDE ALL CURRENCIES
                fiat_currencies = []
                for code in sorted(rates.keys()):
                    # Include ALL currencies from API, use code as name if we don't have a friendly name
                    fiat_currencies.append({
                        'code': code,
                        'name': currency_names.get(code, code),  # Use code as fallback if name not found
                        'symbol': currency_symbols.get(code, code),  # Use code as fallback if symbol not found
                        'type': 'fiat'
                    })
                
                # Combine all currencies
                all_currencies = fiat_currencies + crypto_currencies
                
                # Common currencies (top 10 most used)
                common_codes = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR', 'BRL']
                common_currencies = [c for c in fiat_currencies if c['code'] in common_codes]
                
                return jsonify({
                    'all': all_currencies,
                    'fiat': fiat_currencies,
                    'crypto': crypto_currencies,
                    'common': common_currencies,
                    'loaded': True
                })
                
        except Exception:
            pass  # Silent fallback to hardcoded list
        
        # Fallback: Return hardcoded list
        return self._get_fallback_currencies()
    
    def _get_fallback_currencies(self):
        """Fallback currency list if API is unavailable."""
        from src.config.fallback_data import FALLBACK_FIAT_CURRENCIES, FALLBACK_CRYPTO_CURRENCIES
        
        fiat_currencies = FALLBACK_FIAT_CURRENCIES
        crypto_currencies = FALLBACK_CRYPTO_CURRENCIES
        all_currencies = fiat_currencies + crypto_currencies
        
        return jsonify({
            'all': all_currencies,
            'fiat': fiat_currencies,
            'crypto': crypto_currencies,
            'common': fiat_currencies,
            'loaded': True
        })
    
    def get_exchange_rates(self, base_currency):
        """Get exchange rates for a base currency."""
        rates = self._fetch_exchange_rates(base_currency)
        return jsonify(rates)
    
    def _fetch_exchange_rates(self, base_currency='EUR'):
        """Fetch exchange rates from external API or use fallback."""
        try:
            # Try to fetch from API first
            import requests
            
            # Use USD as the API base (most APIs use USD)
            response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                api_rates = data.get('rates', {})
                
                if api_rates:
                    # Add crypto rates (API doesn't include crypto)
                    try:
                        crypto_response = requests.get(
                            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,binancecoin,cardano,solana,ripple&vs_currencies=usd',
                            timeout=3
                        )
                        if crypto_response.status_code == 200:
                            crypto_data = crypto_response.json()
                            # Convert crypto prices to rates (1 USD = X crypto)
                            if 'bitcoin' in crypto_data:
                                api_rates['BTC'] = 1.0 / crypto_data['bitcoin']['usd']
                            if 'ethereum' in crypto_data:
                                api_rates['ETH'] = 1.0 / crypto_data['ethereum']['usd']
                            if 'tether' in crypto_data:
                                api_rates['USDT'] = 1.0 / crypto_data['tether']['usd']
                            if 'binancecoin' in crypto_data:
                                api_rates['BNB'] = 1.0 / crypto_data['binancecoin']['usd']
                            if 'cardano' in crypto_data:
                                api_rates['ADA'] = 1.0 / crypto_data['cardano']['usd']
                            if 'solana' in crypto_data:
                                api_rates['SOL'] = 1.0 / crypto_data['solana']['usd']
                            if 'ripple' in crypto_data:
                                api_rates['XRP'] = 1.0 / crypto_data['ripple']['usd']
                    except:
                        pass  # Continue without crypto rates
                    
                    # API returns rates with USD as base
                    # Convert to requested base currency
                    if base_currency == 'USD':
                        return api_rates
                    elif base_currency in api_rates:
                        # Convert from USD base to requested base
                        base_rate = api_rates[base_currency]
                        converted_rates = {}
                        for currency, rate in api_rates.items():
                            converted_rates[currency] = rate / base_rate
                        return converted_rates
                    else:
                        # Base currency not found, use USD rates
                        return api_rates
        except Exception:
            pass  # Silent fallback to hardcoded rates
        
        # Fallback to configuration file rates
        from src.config.fallback_data import FALLBACK_EXCHANGE_RATES
        fallback_rates = FALLBACK_EXCHANGE_RATES.copy()
        
        # If base is not EUR, convert rates
        if base_currency != 'EUR' and base_currency in fallback_rates:
            base_rate = fallback_rates[base_currency]
            converted_rates = {}
            for currency, rate in fallback_rates.items():
                converted_rates[currency] = rate / base_rate
            return converted_rates
        
        return fallback_rates
    
    def _convert_currency(self, amount, from_currency, to_currency, exchange_rates):
        """Convert amount from one currency to another."""
        if from_currency == to_currency:
            return float(amount)
        
        # Get rate for from_currency (to EUR)
        from_rate = exchange_rates.get(from_currency, 1.0)
        # Get rate for to_currency (from EUR)
        to_rate = exchange_rates.get(to_currency, 1.0)
        
        # Convert: amount -> EUR -> target currency
        amount_in_eur = float(amount) / from_rate
        amount_in_target = amount_in_eur * to_rate
        
        return amount_in_target
