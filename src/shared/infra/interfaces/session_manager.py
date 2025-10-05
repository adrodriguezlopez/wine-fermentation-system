"""
Session manager interface.
"""

from typing import Protocol, AsyncContextManager, runtime_checkable
from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class ISessionManager(Protocol):
    """
    Interface for database session management.
    
    This protocol defines the contract that any session manager implementation
    must follow to provide async database session handling for repositories.
    """
    
    async def get_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Get an async database session within a context manager.
        
        Returns:
            AsyncContextManager[AsyncSession]: Context manager that yields an async session
            
        Usage:
            async with session_manager.get_session() as session:
                # Use session for database operations
                pass
        """
        ...
    
    async def close(self) -> None:
        """
        Close the session manager and cleanup resources.
        
        This should properly dispose of the underlying engine and
        cleanup any pending connections.
        """
        ...