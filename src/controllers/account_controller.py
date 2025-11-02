"""
Account controller for handling account-related API endpoints.
"""
from flask import request, jsonify, session
from src.services.account_service import AccountService
from src.utils.validation import InputValidator
from src.repositories.exchange_rate_repository import ExchangeRateRepository
from src.services.exchange_rate_service import ExchangeRateService


class AccountController:
    """Controller for account-related operations."""
    
    def __init__(self, account_service: AccountService, db=None):
        """Initialize controller with account service."""
        self.account_service = account_service
        self.exchange_rate_repo = ExchangeRateRepository(db) if db else None
        self.exchange_rate_service = ExchangeRateService(db, self.exchange_rate_repo) if db else None
    
    def _get_current_user_id(self):
        """Get current user ID from session."""
        return session.get('user_id')
    
    def _require_authentication(self):
        """Check if user is authenticated."""
        user_id = self._get_current_user_id()
        if not user_id:
            return None, jsonify({'error': 'Authentication required'}), 401
        return user_id, None, None
    
    def get_accounts(self, currency=None):
        """Get all accounts for current user, grouped by type with currency conversion and sorting."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # If currency is provided in URL, use it; otherwise get from session or default
        if currency is None:
            currency = session.get('currency', 'EUR')
        
        sort_by = request.args.get('sort', 'value-desc')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        # Get USD-based exchange rates once (cached if < 24hrs)
        usd_rates = self.exchange_rate_service.get_usd_rates() if self.exchange_rate_service else None
        if not usd_rates:
            return jsonify({'error': 'Exchange rates unavailable'}), 503
        
        # Get accounts
        accounts = self.account_service.get_user_accounts(user_id, include_archived=include_archived)
        
        # Group assets by type
        savings = []
        equity = []
        credit = []
        
        total_assets = 0.0
        total_liabilities = 0.0
        
        for account in accounts:
            original_value = account['current_value']
            original_currency = account['currency']
            
            # Convert value to target currency using cached USD rates
            converted_value = self.exchange_rate_service.convert_with_cached_rates(
                original_value, original_currency, currency, usd_rates
            )
            
            # If conversion fails (currency not found), return error
            if converted_value is None:
                return jsonify({
                    'error': f'Currency {original_currency} or {currency} not available in exchange rates'
                }), 400
            
            # Create asset object for frontend
            asset_obj = {
                'id': account['id'],
                'name': account['name'],
                'current_value': account['current_value'],
                'value': converted_value,
                'original_value': original_value,
                'currency': currency.upper(),
                'original_currency': original_currency,
                'tag': account.get('tag'),
                'tags': account.get('tags', []),  # Include tags array
                'archived': account.get('archived', False),
                'term_length': account.get('term_length', 0),
                'ownership_ratio': account.get('ownership_ratio', 1.0),
                'note': account.get('note', ''),
                'created_at': account.get('created_at'),
                'updated_at': account.get('updated_at')
            }
            
            # Group by value: negative = liability (credit), positive = asset
            if account['current_value'] < 0:
                credit.append(asset_obj)
                total_liabilities += abs(converted_value)
            else:
                savings.append(asset_obj)
                total_assets += converted_value
        
        # Apply sorting
        def sort_list(items, sort_type):
            if sort_type == 'value-desc':
                return sorted(items, key=lambda x: x['value'], reverse=True)
            elif sort_type == 'value-asc':
                return sorted(items, key=lambda x: x['value'])
            elif sort_type == 'name-asc':
                return sorted(items, key=lambda x: x['name'].lower())
            elif sort_type == 'name-desc':
                return sorted(items, key=lambda x: x['name'].lower(), reverse=True)
            return items
        
        savings = sort_list(savings, sort_by)
        equity = sort_list(equity, sort_by)
        credit = sort_list(credit, sort_by)
        
        net_worth = total_assets - total_liabilities
        
        return jsonify({
            'savings': savings,
            'equity': equity,
            'credit': credit,
            'assets': savings + equity,  # Combined for compatibility
            'liabilities': credit,
            'net_worth': net_worth,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'sort': sort_by
        })
    
    def get_accounts_by_currency(self, currency):
        """Get accounts filtered by currency."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        accounts = self.account_service.get_accounts_by_currency(user_id, currency)
        return jsonify(accounts)
    
    def get_accounts_by_type(self, account_type):
        """Get accounts filtered by type."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        accounts = self.account_service.get_accounts_by_type(user_id, account_type)
        return jsonify(accounts)
    
    def get_account(self, account_id):
        """Get specific account by ID."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        account = self.account_service.get_account_by_id(account_id)
        if account and account['user_id'] == user_id:
            return jsonify(account)
        else:
            return jsonify({'error': 'Account not found'}), 404
    
    def create_account(self):
        """Create a new account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data required'}), 400
        
        # Sanitize and validate input data
        sanitized_data = InputValidator.sanitize_account_data(data)
        
        # Validate required fields
        if not sanitized_data.get('name'):
            return jsonify({'error': 'Valid account name is required'}), 400
        
        if 'current_value' not in sanitized_data:
            return jsonify({'error': 'Valid current value is required'}), 400
        
        if not sanitized_data.get('currency'):
            return jsonify({'error': 'Valid currency code is required'}), 400
        
        result = self.account_service.create_account(user_id, sanitized_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    def update_account(self, account_id):
        """Update an existing account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data required'}), 400
        
        # Sanitize and validate input data
        sanitized_data = InputValidator.sanitize_account_data(data)
        
        result = self.account_service.update_account(account_id, sanitized_data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def update_account_field(self, account_id):
        """Update a single field of an existing account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data required'}), 400
        
        field_name = data.get('field')
        field_value = data.get('value')
        
        if not field_name:
            return jsonify({'error': 'Field name is required'}), 400
        
        # Validate field name
        allowed_fields = ['name', 'account_type', 'current_value', 'currency', 'tag', 'tags', 'archived', 'term_length', 'ownership_ratio', 'note', 'value_change_type']
        if field_name not in allowed_fields:
            return jsonify({'error': 'Invalid field name'}), 400
        
        # Sanitize value based on field type
        if field_name in ['name', 'tag', 'note']:
            field_value = InputValidator.sanitize_string(field_value, 100 if field_name == 'name' else (50 if field_name == 'tag' else 500))
        elif field_name == 'tags':
            # Tags field should be a list of strings
            if not isinstance(field_value, list):
                return jsonify({'error': 'Tags must be an array'}), 400
            # Sanitize each tag
            field_value = [InputValidator.sanitize_string(tag, 50) for tag in field_value if tag and tag.strip()]
        elif field_name == 'currency':
            field_value = field_value.strip().upper() if field_value else ''
            if not InputValidator.validate_currency(field_value):
                return jsonify({'error': 'Invalid currency code'}), 400
        elif field_name == 'account_type':
            field_value = field_value.strip() if field_value else ''
            if not InputValidator.validate_account_type(field_value):
                return jsonify({'error': 'Invalid account type'}), 400
        elif field_name == 'current_value':
            is_valid, decimal_value = InputValidator.validate_decimal(field_value, -999999999.99, 999999999.99)
            if not is_valid:
                return jsonify({'error': 'Invalid current value'}), 400
            field_value = float(decimal_value)
        elif field_name in ['ownership_ratio', 'term_length']:
            is_valid, decimal_value = InputValidator.validate_decimal(field_value, 0.0, 1.0)
            if not is_valid:
                return jsonify({'error': f'Invalid {field_name} (must be between 0.0 and 1.0)'}), 400
            field_value = float(decimal_value)
        elif field_name == 'archived':
            field_value = bool(field_value)
        
        result = self.account_service.update_account_field(account_id, field_name, field_value)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def delete_account(self, account_id):
        """Delete an account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        result = self.account_service.delete_account(account_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def archive_account(self, account_id):
        """Archive an account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        result = self.account_service.archive_account(account_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def unarchive_account(self, account_id):
        """Unarchive an account."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        result = self.account_service.unarchive_account(account_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def get_portfolio_summary(self):
        """Get portfolio summary for current user."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        summary = self.account_service.get_portfolio_summary(user_id)
        return jsonify(summary)
    
    def get_net_worth_history(self):
        """Get historical net worth data."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        currency = request.args.get('currency')
        period = request.args.get('period', 'ytd')  # For future use
        
        history = self.account_service.get_net_worth_history(user_id, currency)
        return jsonify(history)
    
    def get_account_history(self, account_id):
        """Get historical data for a specific account with optional period filtering."""
        from datetime import datetime, timedelta
        
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        period = request.args.get('period', 'max')
        
        # Verify account belongs to user
        account = self.account_service.get_account_by_id(account_id)
        if not account or account['user_id'] != user_id:
            return jsonify({'error': 'Account not found'}), 404
        
        # Calculate start date based on period
        now = datetime.now()
        if period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == '3months':
            start_date = now - timedelta(days=90)
        elif period == '6months':
            start_date = now - timedelta(days=180)
        elif period == 'ytd':
            start_date = datetime(now.year, 1, 1)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        elif period == '2years':
            start_date = now - timedelta(days=365*2)
        elif period == '3years':
            start_date = now - timedelta(days=365*3)
        elif period == '4years':
            start_date = now - timedelta(days=365*4)
        elif period == '5years':
            start_date = now - timedelta(days=365*5)
        else:  # max
            start_date = None
        
        # Get history from account service
        history = self.account_service.get_account_history(account_id, start_date)
        
        # Calculate growth percentage
        growth_percentage = 0.0
        if len(history) >= 2:
            first_value = history[0]['value']
            last_value = history[-1]['value']
            if first_value != 0:
                growth_percentage = ((last_value - first_value) / abs(first_value)) * 100
        
        # Get last updated date from the most recent history entry
        last_updated = 'N/A'
        try:
            if history and len(history) > 0:
                # Get the most recent history entry date
                last_entry = history[-1]
                last_history_date = last_entry.get('date')
                
                if last_history_date:
                    # Parse and format the date
                    parsed_date = datetime.fromisoformat(str(last_history_date).replace('Z', '+00:00').split('T')[0])
                    last_updated = parsed_date.strftime('%b %d, %Y')
            elif account.get('created_at'):
                # Fallback to account creation date if no history
                    parsed_date = datetime.fromisoformat(str(account['created_at']).replace('Z', '+00:00').split('T')[0])
                    last_updated = parsed_date.strftime('%b %d, %Y')
        except Exception:
            last_updated = 'N/A'
        
        return jsonify({
            'account': account,
            'history': history,
            'growth_percentage': round(growth_percentage, 2),
            'last_updated': last_updated,
            'period': period
        })

