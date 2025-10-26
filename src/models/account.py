"""Account model for the financial portfolio application."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class Account:
    """Account entity representing a financial account (asset or liability)."""
    
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    current_value: float = 0.0
    currency: str = "USD"
    tag: Optional[str] = None  # Kept for backward compatibility
    tags: List[str] = field(default_factory=list)  # New: multiple tags support
    archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    term_length: int = 0
    ownership_ratio: float = 1.0
    note: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def get_historical_values(self) -> Dict[str, float]:
        """Get historical values from account_history table."""
        # This is now handled by the account_repository
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'current_value': self.current_value,
            'currency': self.currency,
            'tag': self.tag,  # Keep for backward compatibility
            'tags': self.tags,  # New: list of tags
            'archived': self.archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'term_length': self.term_length,
            'ownership_ratio': self.ownership_ratio,
            'note': self.note
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """Create Account instance from dictionary."""
        account = cls()
        account.id = data.get('id')
        account.user_id = data.get('user_id', 0)
        account.name = data.get('name', '')
        account.current_value = data.get('current_value', 0.0)
        account.currency = data.get('currency', 'USD')
        account.tag = data.get('tag')  # Backward compatibility
        account.tags = data.get('tags', [])  # New: multiple tags
        account.archived = data.get('archived', False)
        account.term_length = data.get('term_length', 0)
        account.ownership_ratio = data.get('ownership_ratio', 1.0)
        account.note = data.get('note')
        
        # Handle datetime fields
        for field_name in ['created_at', 'updated_at']:
            field_value = data.get(field_name)
            if field_value:
                setattr(account, field_name, datetime.fromisoformat(field_value.replace('Z', '+00:00')))
        
        return account
