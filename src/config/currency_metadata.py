"""
Currency metadata configuration.
This file contains static metadata about currencies (names, symbols, crypto list).
These are display/formatting values that rarely change, unlike exchange rates which are dynamic.
"""

# Common currencies (top 10 most used worldwide)
COMMON_CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR', 'BRL']

# Crypto API name to currency code mapping (for CoinGecko API)
CRYPTO_API_MAPPING = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'tether': 'USDT',
    'binancecoin': 'BNB',
    'cardano': 'ADA',
    'solana': 'SOL',
    'ripple': 'XRP'
}

# Extended crypto list (cryptocurrencies supported by the app)
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

# Comprehensive currency names mapping
CURRENCY_NAMES = {
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
    # Additional currencies
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
CURRENCY_SYMBOLS = {
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
