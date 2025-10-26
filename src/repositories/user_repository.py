"""
User repository for database operations.
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
    
    def authenticate(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[User]:
        """Authenticate user by username and password with security enhancements."""
        from datetime import datetime, timedelta
        
        user = self.find_by_username(username)
        
        if not user:
            # Log failed authentication attempt for non-existent user
            self.db.log_security_event(
                user_id=None,
                event_type='LOGIN_FAILED_USER_NOT_FOUND',
                ip_address=ip_address,
                user_agent=user_agent,
                details=f'Login attempt for non-existent username: {username}'
            )
            return None
        
        # Check if account is locked
        if user.is_account_locked():
            self.db.log_security_event(
                user_id=user.id,
                event_type='LOGIN_BLOCKED_ACCOUNT_LOCKED',
                ip_address=ip_address,
                user_agent=user_agent,
                details='Login attempt on locked account'
            )
            return None
        
        # Check if account is active
        if not user.is_active:
            self.db.log_security_event(
                user_id=user.id,
                event_type='LOGIN_BLOCKED_ACCOUNT_INACTIVE',
                ip_address=ip_address,
                user_agent=user_agent,
                details='Login attempt on inactive account'
            )
            return None
        
        # Verify password
        if self.db.verify_password(password, user.password_hash):
            # Successful login - reset failed attempts and update last login
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.last_login = datetime.now()
            self.update(user)
            
            self.db.log_security_event(
                user_id=user.id,
                event_type='LOGIN_SUCCESS',
                ip_address=ip_address,
                user_agent=user_agent,
                details='Successful login'
            )
            return user
        else:
            # Failed password - increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts for 30 minutes
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.now() + timedelta(minutes=30)
                lock_details = f'Account locked after {user.failed_login_attempts} failed attempts'
            else:
                lock_details = f'Failed login attempt #{user.failed_login_attempts}'
            
            self.update(user)
            
            self.db.log_security_event(
                user_id=user.id,
                event_type='LOGIN_FAILED_WRONG_PASSWORD',
                ip_address=ip_address,
                user_agent=user_agent,
                details=lock_details
            )
            return None
    
    def reset_failed_attempts(self, user_id: int) -> bool:
        """Reset failed login attempts for a user."""
        query = '''
        UPDATE users 
        SET failed_login_attempts = 0, account_locked_until = NULL
        WHERE id = ?
        '''
        rows_affected = self.db.execute_update(query, (user_id,))
        return rows_affected > 0