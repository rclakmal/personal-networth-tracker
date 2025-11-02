"""
Tag repository for database operations.
Repository layer should only contain SQL queries, no business logic.
"""
from typing import List
from src.utils.database import DatabaseInterface


class TagRepository:
    """Repository for Tag entity database operations."""
    
    def __init__(self, db: DatabaseInterface):
        """Initialize repository with database interface."""
        self.db = db
    
    def find_all(self) -> List[str]:
        """Get all unique tags."""
        query = 'SELECT name FROM tags ORDER BY name'
        results = self.db.execute_query(query)
        return [row['name'] for row in results]
    
    def find_by_account_id(self, account_id: int) -> List[str]:
        """Get all tags for a specific account."""
        query = '''
        SELECT t.name
        FROM tags t
        INNER JOIN account_tags at ON t.id = at.tag_id
        WHERE at.account_id = ?
        ORDER BY t.name
        '''
        results = self.db.execute_query(query, (account_id,))
        return [row['name'] for row in results]
    
    def find_by_name(self, tag_name: str) -> dict:
        """Find a tag by name."""
        query = 'SELECT id, name FROM tags WHERE name = ?'
        results = self.db.execute_query(query, (tag_name,))
        if results:
            return dict(results[0])
        return None
    
    def create(self, tag_name: str) -> int:
        """Insert a tag if it doesn't exist. Returns tag ID."""
        # Use INSERT OR IGNORE to avoid duplicates
        query = 'INSERT OR IGNORE INTO tags (name) VALUES (?)'
        tag_id = self.db.execute_insert(query, (tag_name,))
        
        # If tag already existed, get its ID
        if tag_id == 0:
            existing_tag = self.find_by_name(tag_name)
            if existing_tag:
                return existing_tag['id']
        
        return tag_id
    
    def link_tag_to_account(self, account_id: int, tag_id: int) -> None:
        """Link a tag to an account."""
        query = 'INSERT OR IGNORE INTO account_tags (account_id, tag_id) VALUES (?, ?)'
        self.db.execute_insert(query, (account_id, tag_id))
    
    def unlink_all_tags_from_account(self, account_id: int) -> int:
        """Remove all tag associations from an account."""
        query = 'DELETE FROM account_tags WHERE account_id = ?'
        rows_affected = self.db.execute_update(query, (account_id,))
        return rows_affected
    
    def unlink_tag_from_account(self, account_id: int, tag_id: int) -> int:
        """Remove a specific tag association from an account."""
        query = 'DELETE FROM account_tags WHERE account_id = ? AND tag_id = ?'
        rows_affected = self.db.execute_update(query, (account_id, tag_id))
        return rows_affected
