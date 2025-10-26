"""Integration tests for database operations"""
import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.database import DatabaseInterface
from repositories.account_repository import AccountRepository
from models.account import Account


class TestDatabaseIntegration(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_interface = DatabaseInterface(self.temp_db.name)
        self.account_repository = AccountRepository(self.db_interface)
    
    def tearDown(self):
        """Clean up temporary database"""
        os.unlink(self.temp_db.name)
    
    def test_create_and_retrieve_account(self):
        """Test creating and retrieving an account"""
        account = Account(
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        created_account = self.account_repository.create(account)
        
        self.assertIsNotNone(created_account.id)
        
        retrieved_account = self.account_repository.find_by_id(created_account.id)
        
        self.assertEqual(retrieved_account.name, "Test Account")
        self.assertEqual(retrieved_account.current_value, 1000.0)
    
    def test_update_account(self):
        """Test updating an account"""
        account = Account(
            user_id=1,
            account_id="TEST-1",
            name="Test Account",
            account_type="Savings",
            current_value=1000.0,
            currency="USD"
        )
        
        created_account = self.account_repository.create(account)
        created_account.current_value = 1500.0
        
        success = self.account_repository.update(created_account)
        
        self.assertTrue(success)
        
        updated_account = self.account_repository.find_by_id(created_account.id)
        self.assertEqual(updated_account.current_value, 1500.0)


if __name__ == '__main__':
    unittest.main()
