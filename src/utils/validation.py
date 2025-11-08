"""
Input validation and sanitization utilities.
"""
import re
import html
from typing import Any, Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime


class DateFormatConverter:
    """Utility class for date format conversion and normalization."""
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """
        Convert various date formats to YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date string in YYYY-MM-DD format or None if invalid
        """
        if not date_str:
            return None
        
        # Remove any quotes or extra whitespace
        date_str = date_str.replace('"', '').replace("'", '').strip()
        
        try:
            # Try to parse various date formats
            date_obj = None
            
            # Format: YYYY-MM-DD or YYYY/MM/DD
            if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', date_str):
                parts = re.split(r'[-/]', date_str)
                date_obj = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            
            # Format: DD/MM/YYYY or DD-MM-YYYY
            elif re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', date_str):
                parts = re.split(r'[-/]', date_str)
                # Assume DD/MM/YYYY (European format)
                date_obj = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            
            # Format: MM/DD/YYYY or MM-DD-YYYY (less common, but check)
            elif re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', date_str):
                parts = re.split(r'[-/]', date_str)
                # Try MM/DD/YYYY if DD/MM/YYYY failed
                try:
                    date_obj = datetime(int(parts[2]), int(parts[0]), int(parts[1]))
                except ValueError:
                    # If MM/DD/YYYY fails, stick with DD/MM/YYYY
                    date_obj = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            
            # Format: YYYYMMDD
            elif re.match(r'^\d{8}$', date_str):
                date_obj = datetime.strptime(date_str, '%Y%m%d')
            
            if date_obj:
                # Validate date is not in the future
                if date_obj > datetime.now():
                    return None
                
                # Return in YYYY-MM-DD format
                return date_obj.strftime('%Y-%m-%d')
                
        except (ValueError, IndexError) as e:
            # Invalid date
            return None
        
        return None
    
    @staticmethod
    def parse_date_with_format(date_str: str, date_format: str) -> Optional[str]:
        """
        Parse date string with specific format and convert to YYYY-MM-DD.
        
        Args:
            date_str: Date string to parse
            date_format: Expected format ('YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD-MM-YYYY')
            
        Returns:
            Date string in YYYY-MM-DD format or None if invalid
        """
        if not date_str or not date_format:
            return None
        
        date_str = date_str.strip()
        
        try:
            date_obj = None
            
            if date_format == 'YYYY-MM-DD':
                match = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', date_str)
                if match:
                    date_obj = datetime(int(match[1]), int(match[2]), int(match[3]))
            
            elif date_format == 'DD/MM/YYYY':
                match = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', date_str)
                if match:
                    date_obj = datetime(int(match[3]), int(match[2]), int(match[1]))
            
            elif date_format == 'MM/DD/YYYY':
                match = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', date_str)
                if match:
                    date_obj = datetime(int(match[3]), int(match[1]), int(match[2]))
            
            elif date_format == 'DD-MM-YYYY':
                match = re.match(r'^(\d{1,2})[-](\d{1,2})[-](\d{4})$', date_str)
                if match:
                    date_obj = datetime(int(match[3]), int(match[2]), int(match[1]))
            
            if date_obj:
                # Validate date is not in the future
                if date_obj > datetime.now():
                    return None
                
                return date_obj.strftime('%Y-%m-%d')
                
        except (ValueError, IndexError):
            return None
        
        return None


class InputValidator:
    """Utility class for input validation and sanitization."""
    
    # Regular expressions for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')  # Any 3-letter currency code
    ACCOUNT_TYPE_PATTERN = re.compile(r'^(Savings|Equity|Credit)$')
    
    @staticmethod
    def sanitize_string(value: Any, max_length: int = 255) -> str:
        """Sanitize and validate string input."""
        if value is None:
            return ""
        
        # Convert to string and strip whitespace
        sanitized = str(value).strip()
        
        # HTML escape to prevent XSS
        sanitized = html.escape(sanitized)
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:  # RFC 5321 limit
            return False
        return InputValidator.EMAIL_PATTERN.match(email.strip()) is not None
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        if not username:
            return False
        return InputValidator.USERNAME_PATTERN.match(username.strip()) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password is too long"
        
        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password strength (boolean return)."""
        is_valid, _ = InputValidator.validate_password(password)
        return is_valid
    
    @staticmethod
    def validate_currency(currency: str) -> bool:
        """Validate currency code format."""
        if not currency:
            return False
        return InputValidator.CURRENCY_PATTERN.match(currency.strip().upper()) is not None
    
    @staticmethod
    def validate_account_type(account_type: str) -> bool:
        """Validate account type."""
        if not account_type:
            return False
        return InputValidator.ACCOUNT_TYPE_PATTERN.match(account_type.strip()) is not None
    
    @staticmethod
    def validate_decimal(value: Any, min_value: float = None, max_value: float = None) -> tuple[bool, Optional[Decimal]]:
        """Validate and convert to decimal."""
        try:
            decimal_value = Decimal(str(value))
            
            if min_value is not None and decimal_value < Decimal(str(min_value)):
                return False, None
            
            if max_value is not None and decimal_value > Decimal(str(max_value)):
                return False, None
            
            return True, decimal_value
        except (InvalidOperation, ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_integer(value: Any, min_value: int = None, max_value: int = None) -> tuple[bool, Optional[int]]:
        """Validate and convert to integer."""
        try:
            int_value = int(value)
            
            if min_value is not None and int_value < min_value:
                return False, None
            
            if max_value is not None and int_value > max_value:
                return False, None
            
            return True, int_value
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def sanitize_account_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize account data dictionary."""
        sanitized = {}
        
        # Sanitize string fields
        if 'name' in data:
            sanitized['name'] = InputValidator.sanitize_string(data['name'], 100)
        
        if 'tag' in data:
            sanitized['tag'] = InputValidator.sanitize_string(data['tag'], 50)
        
        # Sanitize tags array
        if 'tags' in data:
            if isinstance(data['tags'], list):
                # Sanitize each tag and filter out empty ones
                sanitized['tags'] = [
                    InputValidator.sanitize_string(tag, 50) 
                    for tag in data['tags'] 
                    if tag and str(tag).strip()
                ]
            else:
                sanitized['tags'] = []
        
        if 'note' in data:
            sanitized['note'] = InputValidator.sanitize_string(data['note'], 500)
        
        if 'account_number' in data:
            sanitized['account_number'] = InputValidator.sanitize_string(data['account_number'], 50)
        
        # Validate and sanitize currency
        if 'currency' in data:
            currency = data['currency'].strip().upper() if data['currency'] else ''
            if InputValidator.validate_currency(currency):
                sanitized['currency'] = currency
        
        # Validate account type
        if 'account_type' in data:
            account_type = data['account_type'].strip() if data['account_type'] else ''
            if InputValidator.validate_account_type(account_type):
                sanitized['account_type'] = account_type
        
        # Validate current value
        if 'current_value' in data:
            is_valid, decimal_value = InputValidator.validate_decimal(
                data['current_value'], 
                min_value=-999999999.99, 
                max_value=999999999.99
            )
            if is_valid:
                sanitized['current_value'] = float(decimal_value)
        
        # Validate ownership ratio
        if 'ownership_ratio' in data:
            is_valid, decimal_value = InputValidator.validate_decimal(
                data['ownership_ratio'], 
                min_value=0.0, 
                max_value=1.0
            )
            if is_valid:
                sanitized['ownership_ratio'] = float(decimal_value)
        
        # Validate term length
        if 'term_length' in data:
            is_valid, decimal_value = InputValidator.validate_decimal(
                data['term_length'], 
                min_value=0.0, 
                max_value=1.0
            )
            if is_valid:
                sanitized['term_length'] = float(decimal_value)
        
        # Boolean fields
        if 'archived' in data:
            sanitized['archived'] = bool(data['archived'])
        
        return sanitized
    
    @staticmethod
    def sanitize_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize user data dictionary."""
        sanitized = {}
        
        # Sanitize username
        if 'username' in data:
            username = InputValidator.sanitize_string(data['username'], 30)
            if InputValidator.validate_username(username):
                sanitized['username'] = username
        
        # Sanitize email
        if 'email' in data:
            email = InputValidator.sanitize_string(data['email'], 254)
            if InputValidator.validate_email(email):
                sanitized['email'] = email.lower()  # Store emails in lowercase
        
        # Password validation is handled separately during creation/update
        if 'password' in data:
            sanitized['password'] = data['password']  # Don't sanitize passwords
        
        return sanitized