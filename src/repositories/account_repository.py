"""
Account repository for database operations.
Repository layer should only contain SQL queries, no business logic.
"""
from typing import Optional, List
from src.models.account import Account
from src.utils.database import DatabaseInterface


class AccountRepository:
    """Repository for Account entity database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def find_by_id(self, account_id: int) -> Optional[Account]:
        """Find account by ID (without tags - use TagRepository separately)."""
        query = "SELECT * FROM accounts WHERE id = ?"
        results = self.db.execute_query(query, (account_id,))
        
        if results:
            return Account.from_dict(results[0])
        return None
    
    def find_by_user_id(self, user_id: int) -> List[Account]:
        """Find all accounts for a user (without tags - use TagRepository separately)."""
        query = "SELECT * FROM accounts WHERE user_id = ? ORDER BY name"
        results = self.db.execute_query(query, (user_id,))
        return [Account.from_dict(row) for row in results]
    
    def find_active_by_user_id(self, user_id: int) -> List[Account]:
        """Find all active (non-archived) accounts for a user (without tags - use TagRepository separately)."""
        query = "SELECT * FROM accounts WHERE user_id = ? AND archived = FALSE ORDER BY name"
        results = self.db.execute_query(query, (user_id,))
        return [Account.from_dict(row) for row in results]
    
    def find_by_currency(self, user_id: int, currency: str) -> List[Account]:
        """Find all accounts for a user in specific currency."""
        query = "SELECT * FROM accounts WHERE user_id = ? AND currency = ? ORDER BY name"
        results = self.db.execute_query(query, (user_id, currency))
        return [Account.from_dict(row) for row in results]
    
    def find_with_latest_value_by_user_id(self, user_id: int) -> List[dict]:
        """Get all accounts with their latest values from history."""
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
        results = self.db.execute_query(query, (user_id,))
        return [dict(row) for row in results]
    
    def create(self, account: Account) -> Account:
        """Create a new account (tags are handled separately by TagRepository)."""
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
        return account
    
    def update(self, account: Account) -> bool:
        """Update an existing account (tags are handled separately by TagRepository)."""
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
        
        return rows_affected > 0
    
    def delete(self, account_id: int) -> bool:
        """Delete an account by ID (history is handled separately by AccountHistoryRepository)."""
        query = "DELETE FROM accounts WHERE id = ?"
        rows_affected = self.db.execute_update(query, (account_id,))
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

