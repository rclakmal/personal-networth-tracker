"""
Account history repository for database operations.
Repository layer should only contain SQL queries, no business logic.
"""
from typing import Optional, List
from datetime import datetime, date
from src.models.account_history import AccountHistory
from src.utils.database import DatabaseInterface


class AccountHistoryRepository:
    """Repository for AccountHistory entity database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def create(self, history: AccountHistory) -> AccountHistory:
        """Insert a history entry for an account."""
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
    
    def find_by_account_id(self, account_id: int, limit: Optional[int] = None) -> List[AccountHistory]:
        """Get history entries for an account."""
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
    
    def find_by_account_id_and_date_range(self, account_id: int, start_date: date, end_date: date) -> List[dict]:
        """Get history entries for an account within a date range."""
        query = '''
        SELECT recorded_date as date, value 
        FROM account_history 
        WHERE account_id = ? AND DATE(recorded_date) >= ? AND DATE(recorded_date) <= ?
        ORDER BY recorded_date ASC
        '''
        results = self.db.execute_query(query, (account_id, start_date.isoformat(), end_date.isoformat()))
        return [{'date': row['date'], 'value': row['value']} for row in results]
    
    def find_by_account_id_after_date(self, account_id: int, start_date: date) -> List[dict]:
        """Get history entries for an account after a specific date."""
        query = '''
        SELECT recorded_date as date, value 
        FROM account_history 
        WHERE account_id = ? AND DATE(recorded_date) >= ?
        ORDER BY recorded_date ASC
        '''
        results = self.db.execute_query(query, (account_id, start_date.isoformat()))
        return [{'date': row['date'], 'value': row['value']} for row in results]
    
    def find_last_before_date(self, account_id: int, before_date: date) -> Optional[dict]:
        """Get the last history entry before a specific date."""
        query = '''
        SELECT recorded_date as date, value 
        FROM account_history 
        WHERE account_id = ? AND DATE(recorded_date) < ?
        ORDER BY recorded_date DESC
        LIMIT 1
        '''
        results = self.db.execute_query(query, (account_id, before_date.isoformat()))
        if results:
            return {'date': results[0]['date'], 'value': results[0]['value']}
        return None
    
    def find_all_by_account_id(self, account_id: int) -> List[dict]:
        """Get all history entries for an account."""
        query = '''
        SELECT recorded_date as date, value 
        FROM account_history 
        WHERE account_id = ?
        ORDER BY recorded_date ASC
        '''
        results = self.db.execute_query(query, (account_id,))
        return [{'date': row['date'], 'value': row['value']} for row in results]
    
    def delete_by_account_and_date(self, account_id: int, target_date: date) -> int:
        """Delete history entries for a specific account and date."""
        query = '''
        DELETE FROM account_history 
        WHERE account_id = ? 
        AND DATE(recorded_date) = DATE(?)
        '''
        rows_affected = self.db.execute_update(query, (account_id, target_date.isoformat()))
        return rows_affected
    
    def delete_by_account_id(self, account_id: int) -> int:
        """Delete all history entries for an account."""
        query = "DELETE FROM account_history WHERE account_id = ?"
        rows_affected = self.db.execute_update(query, (account_id,))
        return rows_affected
    
    def find_earliest_date_for_user(self, user_id: int) -> Optional[date]:
        """Get the earliest recorded date for any account belonging to a user."""
        query = '''
        SELECT MIN(DATE(recorded_date)) as earliest_date
        FROM account_history ah
        INNER JOIN accounts a ON ah.account_id = a.id
        WHERE a.user_id = ?
        '''
        results = self.db.execute_query(query, (user_id,))
        if results and results[0]['earliest_date']:
            return datetime.strptime(results[0]['earliest_date'], '%Y-%m-%d').date()
        return None
    
    def find_by_user_and_date_range(self, user_id: int, start_date: date, end_date: date) -> List[dict]:
        """Get all history entries for a user's accounts within a date range."""
        query = '''
        SELECT DATE(ah.recorded_date) as date, ah.account_id, ah.value, a.currency, a.archived
        FROM account_history ah
        INNER JOIN accounts a ON ah.account_id = a.id
        WHERE a.user_id = ? AND DATE(ah.recorded_date) >= ? AND DATE(ah.recorded_date) <= ?
        ORDER BY ah.account_id, ah.recorded_date ASC
        '''
        results = self.db.execute_query(query, (user_id, start_date, end_date))
        return [dict(row) for row in results]
    
    def find_last_before_date_by_user(self, user_id: int, before_date: date) -> List[dict]:
        """Get the most recent value before a date for each account belonging to a user."""
        query = '''
        SELECT ah.account_id, ah.value, a.currency, MAX(DATE(ah.recorded_date)) as last_date
        FROM account_history ah
        INNER JOIN accounts a ON ah.account_id = a.id
        WHERE a.user_id = ? AND DATE(ah.recorded_date) < ?
        GROUP BY ah.account_id
        '''
        results = self.db.execute_query(query, (user_id, before_date))
        return [dict(row) for row in results]
