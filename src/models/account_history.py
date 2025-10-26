"""
Account History model for tracking historical values of accounts.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AccountHistory:
    """Account History entity representing a historical value record for an account."""
    
    id: Optional[int] = None
    account_id: int = 0  # Foreign key to accounts table (id column)
    value: float = 0.0
    currency: str = "USD"
    notes: Optional[str] = None
    date: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.date is None:
            self.date = datetime.now()
