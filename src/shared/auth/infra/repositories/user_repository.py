"""
User repository implementation.

This module implements the IUserRepository interface for database operations
on User entities using SQLAlchemy AsyncSession.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.entities.user import User
from src.shared.auth.domain.errors import UserAlreadyExistsError, UserNotFoundError
from src.shared.auth.domain.interfaces.user_repository_interface import (
    IUserRepository,
)


class UserRepository(IUserRepository):
    """
    Repository implementation for User entity operations.
    
    Implements IUserRepository interface using SQLAlchemy AsyncSession
    for database operations. Handles soft deletes by filtering out
    records where deleted_at is not None.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self._session = session

    async def create(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User entity to create (without ID)
            
        Returns:
            Created User entity with generated ID and timestamps
            
        Raises:
            UserAlreadyExistsError: If email or username already exists
        """
        # Check for duplicate email
        if await self.exists_by_email(user.email):
            raise UserAlreadyExistsError("email", user.email)
        
        # Check for duplicate username
        if await self.exists_by_username(user.username):
            raise UserAlreadyExistsError("username", user.username)
        
        # Set timestamps
        now = datetime.utcnow()
        user.created_at = now
        user.updated_at = now
        
        # Add to session and commit
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Retrieve user by ID, excluding soft-deleted records.
        
        Args:
            user_id: UUID of the user to retrieve
            
        Returns:
            User entity if found and not deleted, None otherwise
        """
        stmt = select(User).where(
            User.id == user_id, User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email, excluding soft-deleted records.
        
        Args:
            email: Email address of the user to retrieve
            
        Returns:
            User entity if found and not deleted, None otherwise
        """
        stmt = select(User).where(
            User.email == email, User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username, excluding soft-deleted records.
        
        Args:
            username: Username of the user to retrieve
            
        Returns:
            User entity if found and not deleted, None otherwise
        """
        stmt = select(User).where(
            User.username == username, User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """
        Update an existing user in the database.
        
        Args:
            user: User entity with updated fields
            
        Returns:
            Updated User entity
            
        Raises:
            UserNotFoundError: If user does not exist or is soft-deleted
        """
        # Verify user exists and is not deleted
        existing = await self.get_by_id(user.id)
        if not existing:
            raise UserNotFoundError(f"User with ID {user.id} not found")
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        # Merge changes and commit
        await self._session.merge(user)
        await self._session.commit()
        await self._session.refresh(user)
        
        return user

    async def delete(self, user_id: UUID) -> bool:
        """
        Soft delete a user by setting deleted_at timestamp.
        
        Args:
            user_id: UUID of the user to delete
            
        Returns:
            True if user was deleted successfully, False if not found
        """
        # Verify user exists
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        # Set deleted_at timestamp on the user object
        user.deleted_at = datetime.utcnow()
        
        # Update in database
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=user.deleted_at)
        )
        await self._session.execute(stmt)
        await self._session.commit()
        
        return True

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with given email exists (excluding deleted).
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists and is not deleted, False otherwise
        """
        stmt = select(func.count(User.id)).where(
            User.email == email, User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def exists_by_username(self, username: str) -> bool:
        """
        Check if a user with given username exists (excluding deleted).
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists and is not deleted, False otherwise
        """
        stmt = select(func.count(User.id)).where(
            User.username == username, User.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0
