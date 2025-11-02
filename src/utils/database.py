"""
Database interface for SQLite operations.
"""
import sqlite3
import bcrypt
import secrets
from contextlib import contextmanager
from typing import Optional, List, Dict, Any


class DatabaseInterface:
    """Database interface using SQLite with proper connection management."""
    
    def __init__(self, database_path: str = 'networth.db'):
        """Initialize database interface with path."""
        self.database_path = database_path
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        # Enable foreign key constraints for data integrity
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table with security enhancements
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP,
                password_reset_token TEXT,
                password_reset_expires TIMESTAMP,
                email_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                preferred_currency TEXT DEFAULT "EUR"
            )
            ''')
            
            # Create accounts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                current_value REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                tag TEXT,
                archived BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                term_length INTEGER DEFAULT 0,
                ownership_ratio REAL DEFAULT 1.0,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Create account history table for tracking account value changes
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                value REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                notes TEXT,
                recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
            ''')
            
            # Create security audit log table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

            # Tags table (for account tagging) and junction table account_tags
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_tags (
                account_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (account_id, tag_id),
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
            ''')

            # Optional index to speed up tag lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)')
            
            # Exchange rates table - USD-based only (simplified)
            # All rates are stored with USD as base currency
            # To convert X to Y: amount_usd = amount_x / rate_x, amount_y = amount_usd * rate_y
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates_usd (
                target_currency TEXT PRIMARY KEY,
                rate REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Index for checking last update time
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_rates_usd_updated ON exchange_rates_usd(last_updated)')
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt for secure storage."""
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its bcrypt hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            self.log_security_event(None, 'password_verification_error', details=str(e))
            return False
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a secure CSRF token."""
        return secrets.token_urlsafe(32)
    
    def log_security_event(self, user_id: Optional[int], event_type: str, 
                          ip_address: str = None, user_agent: str = None, 
                          details: str = None) -> None:
        """Log a security event for auditing purposes."""
        query = '''
        INSERT INTO security_logs (user_id, event_type, ip_address, user_agent, details)
        VALUES (?, ?, ?, ?, ?)
        '''
        self.execute_insert(query, (user_id, event_type, ip_address, user_agent, details))