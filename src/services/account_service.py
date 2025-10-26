"""Account service for business logic operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.account import Account
from src.repositories.account_repository import AccountRepository


class AccountService:
    """Service class for Account business logic."""
    
    def __init__(self, account_repository: AccountRepository):
        """Initialize service with repository."""
        self.account_repository = account_repository
    
    def get_user_accounts(self, user_id: int, include_archived: bool = True) -> List[Dict[str, Any]]:
        """Get all accounts for a user."""
        if include_archived:
            accounts = self.account_repository.find_by_user_id(user_id)
        else:
            accounts = self.account_repository.find_active_by_user_id(user_id)
        
        return [account.to_dict() for account in accounts]
    
    def get_accounts_by_currency(self, user_id: int, currency: str) -> List[Dict[str, Any]]:
        """Get accounts for a user filtered by currency."""
        accounts = self.account_repository.find_by_currency(user_id, currency)
        return [account.to_dict() for account in accounts]
    
    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        account = self.account_repository.find_by_id(account_id)
        return account.to_dict() if account else None
    
    def get_account_by_asset_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get account by external asset_id."""
        account = self.account_repository.find_by_asset_id(asset_id)
        return account.to_dict() if account else None
    
    def create_account(self, user_id: int, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account with validation and auto-generated IDs."""
        from src.models.account_history import AccountHistory
        
        # Validate required fields (removed account_type as it's now computed)
        required_fields = ['name', 'currency']
        for field in required_fields:
            if field not in account_data or not account_data[field]:
                return {'success': False, 'error': f'Field {field} is required'}
        
        # Get current value
        current_value = account_data.get('current_value', 0.0)
        
        # Create account
        account = Account(
            user_id=user_id,
            name=account_data['name'],
            currency=account_data['currency'],
            current_value=current_value,
            tag=account_data.get('tag'),
            tags=account_data.get('tags', []),  # Support multiple tags
            archived=account_data.get('archived', False),
            term_length=account_data.get('term_length', 0.0),
            ownership_ratio=account_data.get('ownership_ratio', 1.0),
            note=account_data.get('note')
        )
        
        try:
            created_account = self.account_repository.create(account)
            
            # Create initial history entry with current value
            history_entry = AccountHistory(
                account_id=created_account.id,
                date=datetime.now(),
                value=current_value
            )
            self.account_repository.add_history(history_entry)
            
            return {
                'success': True,
                'asset': created_account.to_dict()
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to create account: {str(e)}'}
    
    def update_account(self, account_id: int, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing account."""
        account = self.account_repository.find_by_id(account_id)
        if not account:
            return {'success': False, 'error': 'Account not found'}
        
        # Track if current_value was updated to decide on history entry
        current_value_updated = 'current_value' in account_data
        old_value = account.current_value
        new_value = account_data.get('current_value', old_value)
        
        # Update fields if provided
        # Updatable fields (removed account_type as it's computed, and value_change_type/export_date as they're removed)
        updatable_fields = [
            'name', 'current_value', 'currency',
            'tag', 'tags', 'archived', 'term_length', 'ownership_ratio', 'note'
        ]
        
        for field in updatable_fields:
            if field in account_data:
                setattr(account, field, account_data[field])
        
        # Update timestamp only if current_value was updated
        if current_value_updated:
            account.updated_at = datetime.now()
        
        try:
            success = self.account_repository.update(account)
            if success:
                # If current_value was updated, handle history
                if current_value_updated and old_value != new_value:
                    self._handle_value_history_update(account.id, new_value, account.currency)
                
                return {'success': True, 'asset': account.to_dict()}
            else:
                return {'success': False, 'error': 'Failed to update account'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to update account: {str(e)}'}
    
    def update_account_field(self, account_id: int, field_name: str, field_value: Any) -> Dict[str, Any]:
        """Update a single field of an account."""
        account = self.account_repository.find_by_id(account_id)
        if not account:
            return {'success': False, 'error': 'Account not found'}
        
        # Validate field is updatable (removed account_type as it's computed, and value_change_type as it's removed)
        updatable_fields = [
            'name', 'current_value', 'currency',
            'tag', 'tags', 'archived', 'term_length', 'ownership_ratio', 'note'
        ]
        
        if field_name not in updatable_fields:
            return {'success': False, 'error': f'Field {field_name} is not updatable'}
        
        # Store old values for comparison
        old_value = getattr(account, field_name)
        
        # Special handling for tags field
        if field_name == 'tags':
            # Update tags using repository method
            account.tags = field_value
            try:
                success = self.account_repository.update(account)
                if success:
                    return {'success': True, 'asset': account.to_dict()}
                else:
                    return {'success': False, 'error': 'Failed to update tags'}
            except Exception as e:
                return {'success': False, 'error': f'Failed to update tags: {str(e)}'}
        
        # Update the field
        setattr(account, field_name, field_value)
        
        # Update timestamp only if current_value was updated
        if field_name == 'current_value':
            account.updated_at = datetime.now()
        
        try:
            success = self.account_repository.update(account)
            if success:
                # If current_value was updated, handle history
                if field_name == 'current_value' and old_value != field_value:
                    self._handle_value_history_update(account.id, field_value, account.currency)
                
                return {'success': True, 'asset': account.to_dict()}
            else:
                return {'success': False, 'error': 'Failed to update account'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to update account: {str(e)}'}
    
    def _handle_value_history_update(self, account_id: int, new_value: float, currency: str):
        """Handle history updates when current_value changes."""
        from src.models.account_history import AccountHistory
        from datetime import datetime, date
        
        today = date.today()
        
        # Delete any existing history entries for today
        self.account_repository.delete_history_for_date(account_id, today)
        
        # Add new history entry for today
        history_entry = AccountHistory(
            account_id=account_id,
            date=datetime.now(),
            value=new_value,
            currency=currency
        )
        self.account_repository.add_history(history_entry)
    def delete_account(self, account_id: int) -> Dict[str, Any]:
        """Delete an account."""
        try:
            success = self.account_repository.delete(account_id)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Account not found'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to delete account: {str(e)}'}
    
    def archive_account(self, account_id: int) -> Dict[str, Any]:
        """Archive an account (soft delete) and set its value to 0."""
        return self.update_account(account_id, {'archived': True, 'current_value': 0.0})
    
    def unarchive_account(self, account_id: int) -> Dict[str, Any]:
        """Unarchive an account."""
        return self.update_account(account_id, {'archived': False})
    
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio summary for a user."""
        all_accounts = self.account_repository.find_by_user_id(user_id)
        active_accounts = [account for account in all_accounts if not account.archived]
        
        # Group by currency
        currencies = {}
        for account in active_accounts:
            if account.currency not in currencies:
                currencies[account.currency] = {
                    'total_value': 0.0,
                    'account_count': 0,
                    'accounts_by_type': {}
                }
            
            currencies[account.currency]['total_value'] += account.current_value
            currencies[account.currency]['account_count'] += 1
            
            # Group by value: negative = liability, positive = asset
            group_type = 'Liability' if account.current_value < 0 else 'Asset'
            if group_type not in currencies[account.currency]['accounts_by_type']:
                currencies[account.currency]['accounts_by_type'][group_type] = {
                    'count': 0,
                    'total_value': 0.0
                }
            
            currencies[account.currency]['accounts_by_type'][group_type]['count'] += 1
            currencies[account.currency]['accounts_by_type'][group_type]['total_value'] += account.current_value
        
        return {
            'total_accounts': len(all_accounts),
            'active_accounts': len(active_accounts),
            'archived_accounts': len(all_accounts) - len(active_accounts),
            'currencies': currencies
        }
    
    def get_net_worth_history(self, user_id: int, currency: str = None) -> Dict[str, Any]:
        """Get historical net worth data for charts."""
        if currency:
            accounts = self.account_repository.find_by_currency(user_id, currency)
        else:
            accounts = self.account_repository.find_active_by_user_id(user_id)
        
        # Aggregate historical data
        all_timestamps = set()
        for account in accounts:
            all_timestamps.update(account.values_dict.keys())
        
        # Sort timestamps
        sorted_timestamps = sorted([int(ts) for ts in all_timestamps])
        
        # Calculate net worth for each timestamp
        net_worth_data = []
        for timestamp in sorted_timestamps:
            total_value = 0.0
            for account in accounts:
                # Get value at or before this timestamp
                account_values = {int(k): v for k, v in account.values_dict.items()}
                applicable_timestamps = [ts for ts in account_values.keys() if ts <= timestamp]
                if applicable_timestamps:
                    latest_timestamp = max(applicable_timestamps)
                    total_value += account_values[latest_timestamp]
            
            net_worth_data.append({
                'timestamp': timestamp,
                'value': total_value,
                'date': datetime.fromtimestamp(timestamp / 1000).isoformat()
            })
        
        return {
            'currency': currency or 'mixed',
            'data': net_worth_data
        }
    
    def get_account_history(self, account_id: int, start_date=None) -> list:
        """Get historical data for a specific account."""
        from datetime import datetime, timedelta
        
        # Get history from database
        if start_date:
            query = """
            SELECT recorded_date as date, value 
            FROM account_history 
            WHERE account_id = ? AND recorded_date >= ?
            ORDER BY recorded_date ASC
            """
            results = self.account_repository.db.execute_query(
                query, (account_id, start_date.date().isoformat())
            )
            
            # Get the last known value before the period start
            pre_period_query = """
            SELECT recorded_date as date, value 
            FROM account_history 
            WHERE account_id = ? AND recorded_date < ?
            ORDER BY recorded_date DESC
            LIMIT 1
            """
            pre_period_results = self.account_repository.db.execute_query(
                pre_period_query, (account_id, start_date.date().isoformat())
            )
            
            history = []
            
            # Add pre-period value at the start date as opening balance
            if pre_period_results:
                history.append({
                    'date': start_date.date().isoformat(),
                    'value': pre_period_results[0]['value']
                })
            
            # Add all the period results
            if results:
                history.extend([{'date': row['date'], 'value': row['value']} for row in results])
            
            # Add current value if last entry is old
            if history:
                account = self.get_account_by_id(account_id)
                last_date = datetime.fromisoformat(history[-1]['date'].split('T')[0]).date()
                if (datetime.now().date() - last_date).days > 0:
                    history.append({
                        'date': datetime.now().date().isoformat(),
                        'value': account['current_value']
                    })
            
            return history
        else:
            # For "max" period, get all history
            query = """
            SELECT recorded_date as date, value 
            FROM account_history 
            WHERE account_id = ?
            ORDER BY recorded_date ASC
            """
            results = self.account_repository.db.execute_query(query, (account_id,))
            history = [{'date': row['date'], 'value': row['value']} for row in results]
            
            # Add current value if last entry is old
            if history:
                account = self.get_account_by_id(account_id)
                last_date = datetime.fromisoformat(history[-1]['date'].split('T')[0]).date()
                if (datetime.now().date() - last_date).days > 0:
                    history.append({
                        'date': datetime.now().date().isoformat(),
                        'value': account['current_value']
                    })
            
            return history

