"""Unit tests for Account service"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.account_service import AccountService
from repositories.account_repository import AccountRepository
from models.account import Account
from unittest.mock import Mock, MagicMock


class TestAccountService(unittest.TestCase):
    """Test AccountService business logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=AccountRepository)
        self.service = AccountService(self.mock_repository)
    
    def test_get_user_accounts(self):
        """Test getting user accounts"""
        mock_account = Account(
            id=1,
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        self.mock_repository.find_by_user_id.return_value = [mock_account]
        
        result = self.service.get_user_accounts(1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], "Test Account")
        self.mock_repository.find_by_user_id.assert_called_once_with(1)
    
    def test_create_account_success(self):
        """Test successful account creation"""
        account_data = {
            'name': "New Account",
            'account_type': "Savings",
            'currency': "USD",
            'current_value': 1000.0
        }
        
        mock_created_account = Account(
            id=1,
            user_id=1,
            account_id="ACCT-1-123456",
            **account_data
        )
        
        self.mock_repository.find_by_asset_id.return_value = None
        self.mock_repository.create.return_value = mock_created_account
        self.mock_repository.add_history = Mock()
        
        result = self.service.create_account(1, account_data)
        
        self.assertTrue(result['success'])
        self.assertIn('asset', result)
    
    def test_create_account_missing_required_field(self):
        """Test account creation with missing required field"""
        account_data = {
            'name': "New Account",
            'currency': "USD"
            # Missing account_type
        }
        
        result = self.service.create_account(1, account_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
