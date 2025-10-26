"""Unit tests for Account model"""
import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.account import Account


class TestAccountModel(unittest.TestCase):
    """Test Account model functionality"""
    
    def test_account_creation(self):
        """Test basic account creation"""
        account = Account(
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        self.assertEqual(account.user_id, 1)
        self.assertEqual(account.account_id, "TEST-1")
        self.assertEqual(account.name, "Test Account")
        self.assertEqual(account.current_value, 1000.0)
    
    def test_account_to_dict(self):
        """Test account serialization to dictionary"""
        account = Account(
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        account_dict = account.to_dict()
        
        self.assertEqual(account_dict['user_id'], 1)
        self.assertEqual(account_dict['account_id'], "TEST-1")
        self.assertEqual(account_dict['asset_id'], "TEST-1")  # Alias
        self.assertEqual(account_dict['name'], "Test Account")
    
    def test_account_from_dict(self):
        """Test account deserialization from dictionary"""
        data = {
            'user_id': 1,
            'account_id': "TEST-1",
            'name': "Test Account",
            'account_type': "Savings",
            'current_value': 1000.0,
            'currency': "USD"
        }
        
        account = Account.from_dict(data)
        
        self.assertEqual(account.user_id, 1)
        self.assertEqual(account.account_id, "TEST-1")
        self.assertEqual(account.name, "Test Account")
    
    def test_values_dict_property(self):
        """Test values dictionary property"""
        account = Account(
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        account.values_dict = {"1234567890": 500.0, "1234567900": 1000.0}
        
        self.assertEqual(len(account.values_dict), 2)
        self.assertEqual(account.values_dict["1234567890"], 500.0)


if __name__ == '__main__':
    unittest.main()
