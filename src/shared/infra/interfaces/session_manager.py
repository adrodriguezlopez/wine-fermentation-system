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
    
    Transaction Coordination (ADR-031):
    For cross-module transaction coordination, implementations should support
    begin/commit/rollback methods to enable TransactionScope pattern.
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
    
    async def begin(self) -> None:
        """
        Begin a new transaction.
        
        Used by TransactionScope to coordinate multiple services
        in a single transaction. Optional method - implementations
        may no-op if transaction is already active.
        
        Note: Not all implementations need explicit begin() - some
        (like SharedSessionManager) participate in existing transactions.
        """
        ...
    
    async def commit(self) -> None:
        """
        Commit the active transaction.
        
        Used by TransactionScope to commit coordinated operations.
        Implementations should ensure all changes are persisted.
        """
        ...
    
    async def rollback(self) -> None:
        """
        Rollback the active transaction.
        
        Used by TransactionScope on exception to undo changes.
        Implementations should restore database to pre-transaction state.
        """
        ...