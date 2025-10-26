"""
User service for business logic operations.
"""
from typing import Optional, List, Dict, Any
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.database import DatabaseInterface


class UserService:
    """Service class for User business logic."""
    
    def __init__(self, user_repository: UserRepository):
        """Initialize service with repository."""
        self.user_repository = user_repository
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[User]:
        """Authenticate user credentials with security enhancements."""
        return self.user_repository.authenticate(username, password, ip_address, user_agent)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.find_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.user_repository.find_by_username(username)
    
    def create_user(self, username: str, email: str, password: str, portfolio_type: str = 'empty') -> Dict[str, Any]:
        """Create a new user with validation and optional sample portfolio."""
        # Validate input
        if not username or not email or not password:
            return {'success': False, 'error': 'All fields are required'}
        
        # Check if username already exists
        if self.user_repository.find_by_username(username):
            return {'success': False, 'error': 'Username already exists'}
        
        # Check if email already exists
        if self.user_repository.find_by_email(email):
            return {'success': False, 'error': 'Email already exists'}
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=DatabaseInterface.hash_password(password)
        )
        
        try:
            created_user = self.user_repository.create(user)
            
            # Create sample portfolio if requested
            if portfolio_type == 'sample':
                self._create_sample_portfolio(created_user.id)
            
            return {
                'success': True,
                'user': created_user.to_dict()
            }
        except Exception as e:
            return {'success': False, 'error': f'Failed to create user: {str(e)}'}
    
    def _create_sample_portfolio(self, user_id: int):
        """Create sample accounts for new user."""
        from datetime import datetime, timedelta
        from src.repositories.account_repository import AccountRepository
        from src.models.account import Account
        from src.models.account_history import AccountHistory
        
        # Get account repository
        account_repo = AccountRepository(self.user_repository.db)
        
        # Sample assets (account_type is now computed based on current_value)
        sample_assets = [
            {
                'name': 'Savings Account',
                'currency': 'USD',
                'current_value': 5000.00,
                'tag': 'Emergency Fund',
                'term_length': 0.8,  # Very High liquidity
                'ownership_ratio': 1.0  # 100%
            },
            {
                'name': 'Stock Portfolio',
                'currency': 'USD',
                'current_value': 15000.00,
                'tag': 'Investments',
                'term_length': 0.6,  # High liquidity
                'ownership_ratio': 1.0
            },
            {
                'name': 'Credit Card',
                'currency': 'USD',
                'current_value': -2500.00,  # Negative for liability (will be computed as 'Credit')
                'tag': 'Debt',
                'term_length': 0.8,  # Very High liquidity
                'ownership_ratio': 1.0
            },
            {
                'name': 'Retirement Fund',
                'currency': 'USD',
                'current_value': 45000.00,
                'tag': 'Retirement',
                'term_length': 0.0,  # Very Low liquidity (locked)
                'ownership_ratio': 1.0
            }
        ]
        
        current_time = datetime.now()
        
        for idx, account_data in enumerate(sample_assets):
            # Create account (account_type is now computed from current_value)
            account = Account(
                user_id=user_id,
                name=account_data['name'],
                currency=account_data['currency'],
                current_value=account_data['current_value'],
                tag=account_data['tag'],
                term_length=account_data['term_length'],
                ownership_ratio=account_data['ownership_ratio'],
                archived=False
            )
            
            created_account = account_repo.create(account)
            
            # Create historical data for the past year (365 days)
            # Add data points every week (52 points total)
            num_points = 52
            days_back = 365
            
            for point in range(num_points):
                days_ago = days_back - (point * (days_back // (num_points - 1)))
                history_date = current_time - timedelta(days=days_ago)
                
                # Calculate value with some growth/fluctuation
                # For liabilities (negative values), the absolute value decreases over time
                is_liability = account_data['current_value'] < 0
                base_value = abs(account_data['current_value'])
                
                if is_liability:
                    # Liability: starts higher, decreases over time (paying it off)
                    progress = point / (num_points - 1)
                    historical_value = -(base_value * (1.5 - 0.5 * progress))
                else:
                    # Asset: grows over time with some random fluctuation
                    progress = point / (num_points - 1)
                    growth_factor = 0.6 + 0.4 * progress  # 40% growth over 1 year
                    # Add small random-like fluctuation based on index
                    fluctuation = 0.03 * ((point * 7) % 11 - 5) / 5  # ±3% variation
                    historical_value = base_value * growth_factor * (1 + fluctuation)
                
                history_entry = AccountHistory(
                    account_id=created_account.id,
                    date=history_date,
                    value=historical_value,
                    currency=account_data['currency']
                )
                account_repo.add_history(history_entry)
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Update user information."""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Update fields if provided
        if 'username' in kwargs:
            user.username = kwargs['username']
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'password' in kwargs:
            user.password_hash = DatabaseInterface.hash_password(kwargs['password'])
        if 'preferred_currency' in kwargs:
            # Validate currency code
            from src.utils.validation import InputValidator
            if not InputValidator.validate_currency(kwargs['preferred_currency']):
                return {'success': False, 'error': 'Invalid currency code'}
            user.preferred_currency = kwargs['preferred_currency'].upper()
        
        try:
            success = self.user_repository.update(user)
            if success:
                return {'success': True, 'user': user.to_dict()}
            else:
                return {'success': False, 'error': 'Failed to update user'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to update user: {str(e)}'}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete a user."""
        try:
            success = self.user_repository.delete(user_id)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to delete user: {str(e)}'}
    
    def change_password(self, user_id: int, current_password: str, new_password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Change user password with verification."""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Verify current password
        db = DatabaseInterface()
        if not db.verify_password(current_password, user.password_hash):
            # Log failed password change attempt
            db.log_security_event(
                user_id=user_id,
                event_type='PASSWORD_CHANGE_FAILED',
                ip_address=ip_address,
                user_agent=user_agent,
                details='Invalid current password provided'
            )
            return {'success': False, 'error': 'Current password is incorrect'}
        
        # Hash new password
        new_password_hash = db.hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        
        try:
            success = self.user_repository.update(user)
            if success:
                # Log successful password change
                db.log_security_event(
                    user_id=user_id,
                    event_type='PASSWORD_CHANGED',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details='Password successfully changed'
                )
                return {'success': True, 'message': 'Password changed successfully'}
            else:
                return {'success': False, 'error': 'Failed to update password'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to change password: {str(e)}'}
    
    def list_users(self) -> List[Dict[str, Any]]:
        """Get all users (for admin purposes)."""
        users = self.user_repository.find_all()
        return [user.to_dict() for user in users]