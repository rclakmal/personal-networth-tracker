"""
User repository for database operations.
Repository layer should only contain SQL queries, no business logic.
"""
from typing import Optional, List
from src.models.user import User
from src.utils.database import DatabaseInterface


class UserRepository:
    """Repository for User entity database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        query = "SELECT * FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        query = "SELECT * FROM users WHERE username = ?"
        results = self.db.execute_query(query, (username,))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.db.execute_query(query, (email,))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def find_all(self) -> List[User]:
        """Get all users."""
        query = "SELECT * FROM users"
        results = self.db.execute_query(query)
        
        return [User.from_dict(row) for row in results]
    
    def create(self, user: User) -> User:
        """Create a new user."""
        query = '''
        INSERT INTO users (username, email, password_hash, created_at, email_verified, is_active, preferred_currency)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        user_id = self.db.execute_insert(query, (
            user.username,
            user.email,
            user.password_hash,
            user.created_at,
            user.email_verified,
            user.is_active,
            user.preferred_currency
        ))
        
        user.id = user_id
        return user
    
    def update(self, user: User) -> bool:
        """Update an existing user."""
        query = '''
        UPDATE users 
        SET username = ?, email = ?, password_hash = ?, last_login = ?, 
            failed_login_attempts = ?, account_locked_until = ?, 
            password_reset_token = ?, password_reset_expires = ?,
            email_verified = ?, is_active = ?, preferred_currency = ?
        WHERE id = ?
        '''
        
        rows_affected = self.db.execute_update(query, (
            user.username,
            user.email,
            user.password_hash,
            user.last_login,
            user.failed_login_attempts,
            user.account_locked_until,
            user.password_reset_token,
            user.password_reset_expires,
            user.email_verified,
            user.is_active,
            user.preferred_currency,
            user.id
        ))
        
        return rows_affected > 0
    
    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        query = "DELETE FROM users WHERE id = ?"
        rows_affected = self.db.execute_update(query, (user_id,))
        return rows_affected > 0
    
    def reset_failed_attempts(self, user_id: int) -> bool:
        """Reset failed login attempts for a user."""
        query = '''
        UPDATE users 
        SET failed_login_attempts = 0, account_locked_until = NULL
        WHERE id = ?
        '''
        rows_affected = self.db.execute_update(query, (user_id,))
        return rows_affected > 0
