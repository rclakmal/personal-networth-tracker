"""
User model for the financial portfolio application.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User entity representing a portfolio owner."""
    
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verified: bool = False
    is_active: bool = True
    preferred_currency: str = "EUR"  # Default currency
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.account_locked_until:
            return datetime.now() < self.account_locked_until
        return False
    
    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_login_attempts': self.failed_login_attempts,
            'email_verified': self.email_verified,
            'is_active': self.is_active,
            'preferred_currency': self.preferred_currency
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User instance from dictionary."""
        user = cls()
        user.id = data.get('id')
        user.username = data.get('username', '')
        user.email = data.get('email', '')
        user.password_hash = data.get('password_hash', '')
        user.failed_login_attempts = data.get('failed_login_attempts', 0)
        user.password_reset_token = data.get('password_reset_token')
        user.email_verified = data.get('email_verified', False)
        user.is_active = data.get('is_active', True)
        user.preferred_currency = data.get('preferred_currency', 'EUR')
        
        # Handle datetime fields
        for field_name in ['created_at', 'last_login', 'account_locked_until', 'password_reset_expires']:
            field_value = data.get(field_name)
            if field_value:
                setattr(user, field_name, datetime.fromisoformat(field_value.replace('Z', '+00:00')))
        
        return user