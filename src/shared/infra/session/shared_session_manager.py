"""
Shared Session Manager for UnitOfWork pattern.

Wraps an existing SQLAlchemy session to be reused across multiple repositories
within a Unit of Work. Prevents session duplication and ensures transaction coordination.

Architecture: Infrastructure Layer (Session Management)

Related Components:
- SessionManager: Creates new sessions (one-per-operation)
- SharedSessionManager: Reuses existing session (many-operations-one-transaction)
- IUnitOfWork: Orchestrates repositories with shared session

Design Pattern: Adapter
- Adapts ISessionManager interface to work with existing session
- Allows repositories to remain agnostic of session source
"""

from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.interfaces.session_manager import ISessionManager


class SharedSessionManager(ISessionManager):
    """
    Session manager that wraps and reuses an existing session.
    
    Used by UnitOfWork to provide same session to multiple repositories,
    ensuring they all participate in the same transaction.
    
    Difference from SessionManager:
    - SessionManager: Creates new session each time (independent transactions)
    - SharedSessionManager: Reuses provided session (coordinated transaction)
    
    Usage:
        ```python
        # Within UnitOfWork
        self._session = await self._session_manager.get_session().__aenter__()
        
        # Provide shared session to repositories
        shared_mgr = SharedSessionManager(self._session)
        self._fermentation_repo = FermentationRepository(shared_mgr)
        self._sample_repo = SampleRepository(shared_mgr)
        
        # Both repos use SAME session/transaction
        ```
    
    Design Principles:
    - Single Responsibility: Only wraps existing session
    - Dependency Inversion: Implements ISessionManager (repository dependency)
    - Transparent: Repositories don't know session is shared
    
    Note: Does NOT close session on context exit - session lifecycle
    managed by UnitOfWork, not individual repositories.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with existing session to be shared.
        
        Args:
            session: Active AsyncSession to wrap and share
        
        Note: Session must be already opened (in transaction)
        """
        self._session = session
    
    def get_session(self) -> AsyncContextManager[AsyncSession]:
        """
        Return context manager that yields the shared session.
        
        Returns:
            AsyncContextManager[AsyncSession]: Context manager for shared session
        
        Design Decision: Why context manager if session already open?
        - Maintains ISessionManager interface contract
        - Allows repositories to use standard pattern: `async with session_mgr.get_session()`
        - No-op context manager (doesn't actually open/close)
        
        Example:
            ```python
            # Repository code (unchanged)
            async with self._session_manager.get_session() as session:
                result = await session.execute(...)
                return result
            
            # Works with both SessionManager and SharedSessionManager!
            ```
        """
        return _SharedSessionContext(self._session)
    
    async def close(self) -> None:
        """
        Close session manager - no-op for shared session.
        
        Session lifecycle managed by owner (UnitOfWork), not by this wrapper.
        """
        pass
    
    async def begin(self) -> None:
        """
        Begin transaction - no-op for shared session.
        
        Shared session already participates in active transaction
        managed by owner. This method exists for ISessionManager
        protocol compliance (ADR-031).
        
        Design Note: TransactionScope may call this, but SharedSessionManager
        doesn't need to do anything since transaction already active.
        """
        pass
    
    async def commit(self) -> None:
        """
        Commit transaction - delegates to underlying session.
        
        Note: In UnitOfWork pattern, UnitOfWork typically manages commit.
        This method exists for TransactionScope compatibility (ADR-031).
        """
        await self._session.commit()
    
    async def rollback(self) -> None:
        """
        Rollback transaction - delegates to underlying session.
        
        Note: In UnitOfWork pattern, UnitOfWork typically manages rollback.
        This method exists for TransactionScope compatibility (ADR-031).
        """
        await self._session.rollback()


class _SharedSessionContext:
    """
    No-op async context manager that yields shared session.
    
    Implements context manager protocol without actually managing
    the session lifecycle. Session remains open after exit.
    
    Private Implementation Detail: Not exposed in public API.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with session to yield.
        
        Args:
            session: Active session to be yielded in context
        """
        self._session = session
    
    async def __aenter__(self) -> AsyncSession:
        """
        Enter context - return shared session.
        
        Returns:
            AsyncSession: The shared session (already open)
        
        Note: Does NOT open session - already open
        """
        return self._session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context - do nothing.
        
        Args:
            exc_type: Exception type (ignored)
            exc_val: Exception value (ignored)
            exc_tb: Exception traceback (ignored)
        
        Note: Does NOT close session - UnitOfWork manages lifecycle
        
        Design Rationale:
        - Repository shouldn't close shared session
        - UnitOfWork owns session, controls commit/rollback/close
        - This is just a pass-through for repository compatibility
        """
        # No-op: UnitOfWork manages session lifecycle
        pass
