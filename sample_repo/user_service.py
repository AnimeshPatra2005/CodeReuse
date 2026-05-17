"""
User service for managing user operations.
"""

from typing import Optional, Dict
from .utils import validate_email, sanitize_string


class User:
    """User model."""
    
    def __init__(self, username: str, email: str, age: int):
        self.username = username
        self.email = email
        self.age = age
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary."""
        return {
            "username": self.username,
            "email": self.email,
            "age": self.age
        }


class UserService:
    """Service for user operations."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
    
    def create_user(self, username: str, email: str, age: int) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            username: Username
            email: Email address
            age: User age
            
        Returns:
            Created user or None if validation fails
        """
        # Sanitize username
        clean_username = sanitize_string(username)
        
        if not clean_username:
            return None
        
        # Validate email
        if not validate_email(email):
            return None
        
        # Check age
        if age < 13:
            return None
        
        # Create user
        user = User(clean_username, email, age)
        self.users[clean_username] = user
        
        return user
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.users.get(username)
    
    def delete_user(self, username: str) -> bool:
        """Delete user by username."""
        if username in self.users:
            del self.users[username]
            return True
        return False

# Made with Bob
