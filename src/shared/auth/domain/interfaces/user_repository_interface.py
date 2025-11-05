"""Repository interface for User entity operations."""

from typing import Optional, Protocol

from ..entities.user import User


class IUserRepository(Protocol):
    """
    Protocol defining User repository operations.
    
    Implementations must provide async database operations for User entity.
    Follows repository pattern with clean separation from business logic.
    """
    
    async def create(self, user: User) -> User:
        """
        Persist a new user to the database.
        
        Args:
            user: User entity to create (id will be generated)
            
        Returns:
            User entity with generated id and timestamps
            
        Raises:
            UserAlreadyExistsError: If email or username already exists
        """
        ...
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by primary key.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User entity if found, None otherwise
        """
        ...
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address (unique constraint).
        
        Args:
            email: User's email address
            
        Returns:
            User entity if found, None otherwise
        """
        ...
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username (unique constraint).
        
        Args:
            username: User's username
            
        Returns:
            User entity if found, None otherwise
        """
        ...
    
    async def update(self, user: User) -> User:
        """
        Update existing user in database.
        
        Args:
            user: User entity with modified fields
            
        Returns:
            Updated User entity with new updated_at timestamp
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        ...
    
    async def delete(self, user_id: int) -> bool:
        """
        Soft delete user (sets deleted_at timestamp).
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if user was deleted, False if not found
        """
        ...
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if user with email exists.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
        """
        ...
    
    async def exists_by_username(self, username: str) -> bool:
        """
        Check if user with username exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        ...
