"""
Base Repository for Wine Fermentation System.

This module provides the base repository class that implements common
database operations, error mapping, multi-tenant scoping, and soft delete
functionality for all domain repositories.
"""

from typing import Protocol, Callable, Awaitable, TypeVar, Any
from sqlalchemy import and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.interfaces.session_manager import ISessionManager

# Import error mapping from fermentation module
# This will be available when BaseRepository is used in domain repositories
try:
    from src.modules.fermentation.src.repository_component.errors import (
        map_database_error,
        RepositoryError
    )
except ImportError:
    # Fallback for testing/development
    def map_database_error(error: Exception) -> Exception:
        return error

    class RepositoryError(Exception):
        pass


T = TypeVar('T')


class BaseRepository:
    """
    Base repository class providing common database operations.

    This class implements:
    - Dependency Inversion through ISessionManager
    - Error mapping integration
    - Multi-tenant scoping for security
    - Soft delete support
    """

    def __init__(self, session_manager: ISessionManager) -> None:
        """
        Initialize BaseRepository with session manager.

        Args:
            session_manager: Session manager implementing ISessionManager protocol

        Raises:
            TypeError: If session_manager doesn't implement ISessionManager
        """
        # Validate that session_manager has the required methods
        required_methods = ['get_session', 'close']
        for method in required_methods:
            if not hasattr(session_manager, method):
                raise TypeError(
                    f"session_manager must implement ISessionManager protocol, "
                    f"missing method: {method}"
                )

        self.session_manager = session_manager

    async def get_session(self):
        """
        Get a database session from the session manager.

        Returns:
            AsyncContextManager[AsyncSession]: Database session context manager
        """
        return await self.session_manager.get_session()

    async def close(self) -> None:
        """
        Close the repository and cleanup resources.

        This delegates to the session manager's close method.
        """
        await self.session_manager.close()

    async def execute_with_error_mapping(self, operation: Callable[[], Awaitable[T]]) -> T:
        """
        Execute a database operation with automatic error mapping.

        Args:
            operation: Async callable that performs the database operation

        Returns:
            Result of the operation

        Raises:
            RepositoryError: Mapped repository error
        """
        try:
            return await operation()
        except Exception as e:
            # Map database errors to repository errors
            raise map_database_error(e) from e

    def scope_query_by_winery_id(self, query, winery_id: int):
        """
        Add winery_id filter to a SQLAlchemy query for multi-tenant security.

        Args:
            query: SQLAlchemy query object
            winery_id: Winery identifier for scoping

        Returns:
            Query with winery_id filter applied

        Raises:
            ValueError: If winery_id is not a valid integer
        """
        if not isinstance(winery_id, int) or winery_id <= 0:
            raise ValueError(f"winery_id must be a positive integer, got {winery_id}")

        # Add winery_id filter - assumes entities have winery_id column
        return query.where(text("winery_id = :winery_id")).params(winery_id=winery_id)

    def apply_soft_delete_filter(self, query, include_deleted: bool = False):
        """
        Apply soft delete filter to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            include_deleted: If True, include soft-deleted records

        Returns:
            Query with soft delete filter applied (if include_deleted=False)
        """
        if include_deleted:
            # Don't apply filter - include all records
            return query

        # Apply soft delete filter - assumes entities have is_deleted column
        # Use IS NULL OR is_deleted = False to handle entities without is_deleted column
        return query.where(text("is_deleted IS NULL OR is_deleted = false"))