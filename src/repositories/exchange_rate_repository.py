"""
Exchange rate repository for managing currency conversion rates in the database.
All rates are stored with USD as the base currency for simplicity.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from src.utils.database import DatabaseInterface


class ExchangeRateRepository:
    """Repository for USD-based exchange rate database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def get_all_rates_usd(self) -> Optional[Dict[str, float]]:
        """
        Get all USD-based exchange rates if not stale (< 24 hours old).
        Returns None if rates are stale or don't exist.
        """
        query = '''
        SELECT target_currency, rate, last_updated 
        FROM exchange_rates_usd
        '''
        results = self.db.execute_query(query)
        
        if not results:
            return None
        
        # Check if any rates are stale (older than 24 hours)
        rates = {}
        oldest_update = None
        
        for row in results:
            last_updated = datetime.fromisoformat(row['last_updated'])
            if oldest_update is None or last_updated < oldest_update:
                oldest_update = last_updated
            rates[row['target_currency']] = row['rate']
        
        # If the oldest rate is stale, return None to trigger refresh
        if oldest_update and datetime.now() - oldest_update >= timedelta(hours=24):
            return None
        
        return rates
    
    def save_rates_bulk_usd(self, rates: Dict[str, float]) -> None:
        """
        Save multiple USD-based exchange rates at once.
        Uses executemany for efficiency.
        """
        if not rates:
            return
            
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prepare all data for batch insert
            insert_data = [
                (target_currency, rate)
                for target_currency, rate in rates.items()
            ]
            
            # Use executemany for batch insert - much faster than individual inserts
            cursor.executemany('''
                INSERT INTO exchange_rates_usd (target_currency, rate, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(target_currency) 
                DO UPDATE SET rate = excluded.rate, last_updated = CURRENT_TIMESTAMP
            ''', insert_data)
            
            conn.commit()
    
    def get_last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent update for USD rates."""
        query = '''
        SELECT MAX(last_updated) as last_update
        FROM exchange_rates_usd
        '''
        results = self.db.execute_query(query)
        
        if results and results[0]['last_update']:
            return datetime.fromisoformat(results[0]['last_update'])
        
        return None
