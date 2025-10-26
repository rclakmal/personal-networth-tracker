"""
Account repository for database operations.
"""
from typing import Optional, List
from src.models.account import Account
from src.models.account_history import AccountHistory
from src.utils.database import DatabaseInterface


class AccountRepository:
    """Repository for Account entity database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def find_by_id(self, account_id: int) -> Optional[Account]:
        """Find account by ID."""
        query = "SELECT * FROM accounts WHERE id = ?"
        results = self.db.execute_query(query, (account_id,))
        
        if results:
            account = Account.from_dict(results[0])
            # Load tags for this account
            account.tags = self._get_account_tags(account_id)
            return account
        return None
    
    def find_by_user_id(self, user_id: int) -> List[Account]:
        """Find all accounts for a user."""
        query = "SELECT * FROM accounts WHERE user_id = ? ORDER BY name"
        results = self.db.execute_query(query, (user_id,))
        
        accounts = [Account.from_dict(row) for row in results]
        # Load tags for each account
        for account in accounts:
            account.tags = self._get_account_tags(account.id)
        return accounts
    
    def find_active_by_user_id(self, user_id: int) -> List[Account]:
        """Find all active (non-archived) accounts for a user."""
        query = "SELECT * FROM accounts WHERE user_id = ? AND archived = FALSE ORDER BY name"
        results = self.db.execute_query(query, (user_id,))
        
        accounts = [Account.from_dict(row) for row in results]
        # Load tags for each account
        for account in accounts:
            account.tags = self._get_account_tags(account.id)
        return accounts
    
    def find_by_currency(self, user_id: int, currency: str) -> List[Account]:
        """Find all accounts for a user in specific currency."""
        query = "SELECT * FROM accounts WHERE user_id = ? AND currency = ? ORDER BY name"
        results = self.db.execute_query(query, (user_id, currency))
        
        return [Account.from_dict(row) for row in results]
    
    def create(self, account: Account) -> Account:
        """Create a new account."""
        query = '''
        INSERT INTO accounts (
            user_id, name, current_value,
            currency, tag, archived, created_at, updated_at,
            term_length, ownership_ratio, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        account_id = self.db.execute_insert(query, (
            account.user_id,
            account.name,
            account.current_value,
            account.currency,
            account.tag,
            account.archived,
            account.created_at,
            account.updated_at,
            account.term_length,
            account.ownership_ratio,
            account.note
        ))
        
        account.id = account_id
        
        # Save tags if provided
        if account.tags:
            self._save_account_tags(account_id, account.tags)
            # Reload tags from database to ensure they're properly set
            account.tags = self._get_account_tags(account_id)
        
        return account
    
    def update(self, account: Account) -> bool:
        """Update an existing account."""
        query = '''
        UPDATE accounts SET
            name = ?, current_value = ?,
            currency = ?, tag = ?, archived = ?, updated_at = ?,
            term_length = ?, ownership_ratio = ?, note = ?
        WHERE id = ?
        '''
        
        rows_affected = self.db.execute_update(query, (
            account.name,
            account.current_value,
            account.currency,
            account.tag,
            account.archived,
            account.updated_at,
            account.term_length,
            account.ownership_ratio,
            account.note,
            account.id
        ))
        
        # Update tags - remove all and re-add
        if rows_affected > 0:
            self._clear_account_tags(account.id)
            if account.tags:
                self._save_account_tags(account.id, account.tags)
        
        return rows_affected > 0
    
    def delete(self, account_id: int) -> bool:
        """Delete an account by ID along with its history."""
        # First delete all history entries
        history_query = "DELETE FROM account_history WHERE account_id = ?"
        self.db.execute_update(history_query, (account_id,))
        
        # Then delete the account
        account_query = "DELETE FROM accounts WHERE id = ?"
        rows_affected = self.db.execute_update(account_query, (account_id,))
        return rows_affected > 0
    
    def get_user_account_count(self, user_id: int) -> int:
        """Get total count of accounts for a user."""
        query = "SELECT COUNT(*) as count FROM accounts WHERE user_id = ?"
        results = self.db.execute_query(query, (user_id,))
        return results[0]['count'] if results else 0
    
    def get_net_worth(self, user_id: int, currency: str = None) -> float:
        """Calculate net worth for a user, optionally filtered by currency."""
        if currency:
            query = '''
            SELECT SUM(current_value) as net_worth 
            FROM accounts 
            WHERE user_id = ? AND currency = ? AND archived = FALSE
            '''
            params = (user_id, currency)
        else:
            query = '''
            SELECT SUM(current_value) as net_worth 
            FROM accounts 
            WHERE user_id = ? AND archived = FALSE
            '''
            params = (user_id,)
        
        results = self.db.execute_query(query, params)
        return results[0]['net_worth'] or 0.0 if results else 0.0
    
    def add_history(self, history: AccountHistory) -> AccountHistory:
        """Add a history entry for an account."""
        from datetime import datetime
        
        query = '''
        INSERT INTO account_history (
            account_id, value, currency, notes, recorded_date
        ) VALUES (?, ?, ?, ?, ?)
        '''
        
        history_id = self.db.execute_insert(query, (
            history.account_id,
            history.value,
            history.currency,
            history.notes,
            history.date
        ))
        
        history.id = history_id
        return history
    
    def get_history(self, account_id: int, limit: Optional[int] = None) -> List[AccountHistory]:
        """Get history entries for an account."""
        from datetime import datetime
        
        if limit:
            query = '''
            SELECT id, account_id, value, currency, notes, recorded_date as date
            FROM account_history 
            WHERE account_id = ? 
            ORDER BY recorded_date DESC 
            LIMIT ?
            '''
            params = (account_id, limit)
        else:
            query = '''
            SELECT id, account_id, value, currency, notes, recorded_date as date
            FROM account_history 
            WHERE account_id = ? 
            ORDER BY recorded_date DESC
            '''
            params = (account_id,)
        
        results = self.db.execute_query(query, params)
        return [AccountHistory(
            id=row['id'],
            account_id=row['account_id'],
            value=row['value'],
            currency=row['currency'],
            notes=row['notes'],
            date=datetime.fromisoformat(row['date']) if row['date'] else None
        ) for row in results]
    
    def delete_history_for_date(self, account_id: int, target_date) -> int:
        """Delete history entries for a specific account and date."""
        from datetime import date
        
        # Convert target_date to date if it's a datetime
        if hasattr(target_date, 'date'):
            target_date = target_date.date()
        
        # Delete entries where the date part matches the target date
        query = '''
        DELETE FROM account_history 
        WHERE account_id = ? 
        AND DATE(recorded_date) = DATE(?)
        '''
        
        rows_affected = self.db.execute_update(query, (account_id, target_date.isoformat()))
        return rows_affected
    
    def _get_account_tags(self, account_id: int) -> List[str]:
        """Get all tags for an account."""
        query = '''
        SELECT t.name
        FROM tags t
        INNER JOIN account_tags at ON t.id = at.tag_id
        WHERE at.account_id = ?
        ORDER BY t.name
        '''
        results = self.db.execute_query(query, (account_id,))
        return [row['name'] for row in results]
    
    def _save_account_tags(self, account_id: int, tags: List[str]) -> None:
        """Save tags for an account."""
        for tag_name in tags:
            if not tag_name or not tag_name.strip():
                continue
            
            tag_name = tag_name.strip()
            
            # Insert tag if it doesn't exist
            tag_insert = 'INSERT OR IGNORE INTO tags (name) VALUES (?)'
            self.db.execute_insert(tag_insert, (tag_name,))
            
            # Get tag ID
            tag_query = 'SELECT id FROM tags WHERE name = ?'
            tag_results = self.db.execute_query(tag_query, (tag_name,))
            
            if tag_results:
                tag_id = tag_results[0]['id']
                
                # Link account to tag
                link_query = 'INSERT OR IGNORE INTO account_tags (account_id, tag_id) VALUES (?, ?)'
                self.db.execute_insert(link_query, (account_id, tag_id))
    
    def _clear_account_tags(self, account_id: int) -> None:
        """Remove all tags from an account."""
        query = 'DELETE FROM account_tags WHERE account_id = ?'
        self.db.execute_update(query, (account_id,))
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags."""
        query = 'SELECT name FROM tags ORDER BY name'
        results = self.db.execute_query(query)
        return [row['name'] for row in results]
