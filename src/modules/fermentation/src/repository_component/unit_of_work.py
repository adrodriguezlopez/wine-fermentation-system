"""
Unit of Work implementation for transactional repository coordination.

Concrete implementation of IUnitOfWork interface providing atomic
multi-repository operations under single database transaction.

Architecture: Repository Component Layer (Infrastructure)

Related ADRs:
- ADR-002: Repository Architecture (specifies UoW pattern)
- ADR-003: Error Handling Architecture

Design Pattern: Unit of Work + Context Manager
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.repositories.lot_source_repository_interface import ILotSourceRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.repository_component.repositories.lot_source_repository import LotSourceRepository
from src.modules.fermentation.src.repository_component.errors import RepositoryError
from src.shared.infra.interfaces.session_manager import ISessionManager
from src.shared.infra.session.shared_session_manager import SharedSessionManager


class UnitOfWork(IUnitOfWork):
    """
    Concrete Unit of Work implementation.
    
    Manages a single database transaction across multiple repositories,
    ensuring atomic operations and data consistency.
    
    Lifecycle:
        1. __aenter__: Begin transaction (open session)
        2. Repository access: Lazy-load repositories with shared session
        3. commit/rollback: Explicit transaction control
        4. __aexit__: Cleanup (auto-rollback if no commit)
    
    Usage Patterns:
    
        Pattern 1 - Explicit Commit (Recommended):
        ```python
        async with uow:
            await uow.fermentation_repo.create(...)
            await uow.sample_repo.create_sample(...)
            await uow.commit()  # Explicit success
        ```
        
        Pattern 2 - Explicit Rollback:
        ```python
        async with uow:
            await uow.fermentation_repo.create(...)
            if error_condition:
                await uow.rollback()
                return
            await uow.commit()
        ```
        
        Pattern 3 - Exception Handling (Auto-rollback):
        ```python
        async with uow:
            await uow.fermentation_repo.create(...)
            raise SomeError()  # Auto-rollback in __aexit__
        ```
    
    Thread Safety: NOT thread-safe (sessions are not thread-safe)
    Concurrency: Safe for asyncio (async/await)
    
    Design Decisions:
    - Lazy Repository Loading: Repos created only when accessed
    - Shared Session: All repos use same session instance
    - Explicit Commit Required: Safe default (no accidental commits)
    - Auto-rollback on Exception: Maintains consistency
    - No Nested Transactions: One UoW = one transaction
    
    State Machine:
        INACTIVE → ACTIVE (enter context)
        ACTIVE → COMMITTED (commit called)
        ACTIVE → ROLLED_BACK (rollback called or exception)
        COMMITTED/ROLLED_BACK → INACTIVE (exit context)
    """
    
    def __init__(self, session_manager: ISessionManager):
        """
        Initialize Unit of Work with session manager.
        
        Args:
            session_manager: Factory for database sessions
        
        Note: Session not created until __aenter__ called
        """
        self._session_manager = session_manager
        
        # State management
        self._session: Optional[AsyncSession] = None
        self._is_active = False
        
        # Lazy-loaded repositories
        self._fermentation_repo: Optional[IFermentationRepository] = None
        self._sample_repo: Optional[ISampleRepository] = None
        self._lot_source_repo: Optional[ILotSourceRepository] = None
    
    @property
    def fermentation_repo(self) -> IFermentationRepository:
        """
        Get fermentation repository sharing this UoW's transaction.
        
        Returns:
            IFermentationRepository: Repository with shared session
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        if not self._is_active:
            raise RuntimeError(
                "Cannot access fermentation_repo outside active UnitOfWork context. "
                "Use 'async with uow:' to activate."
            )
        
        # Lazy initialization
        if self._fermentation_repo is None:
            shared_session_mgr = SharedSessionManager(self._session)
            self._fermentation_repo = FermentationRepository(shared_session_mgr)
        
        return self._fermentation_repo
    
    @property
    def sample_repo(self) -> ISampleRepository:
        """
        Get sample repository sharing this UoW's transaction.
        
        Returns:
            ISampleRepository: Repository with shared session
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        if not self._is_active:
            raise RuntimeError(
                "Cannot access sample_repo outside active UnitOfWork context. "
                "Use 'async with uow:' to activate."
            )
        
        # Lazy initialization
        if self._sample_repo is None:
            shared_session_mgr = SharedSessionManager(self._session)
            self._sample_repo = SampleRepository(shared_session_mgr)
        
        return self._sample_repo
    
    @property
    def lot_source_repo(self) -> ILotSourceRepository:
        """
        Get lot source repository sharing this UoW's transaction.
        
        Returns:
            ILotSourceRepository: Repository with shared session
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        if not self._is_active:
            raise RuntimeError(
                "Cannot access lot_source_repo outside active UnitOfWork context. "
                "Use 'async with uow:' to activate."
            )
        
        # Lazy initialization
        if self._lot_source_repo is None:
            shared_session_mgr = SharedSessionManager(self._session)
            self._lot_source_repo = LotSourceRepository(shared_session_mgr)
        
        return self._lot_source_repo
    
    async def commit(self) -> None:
        """
        Commit the transaction.
        
        Persists all changes made through repositories.
        
        Raises:
            RuntimeError: If called outside active context
            RepositoryError: If commit fails (wraps SQLAlchemy errors)
        
        Note: On failure, automatic rollback is triggered
        """
        if not self._is_active:
            raise RuntimeError(
                "Cannot commit outside active UnitOfWork context. "
                "Use 'async with uow:' to activate."
            )
        
        try:
            await self._session.commit()
        except Exception as e:
            # Auto-rollback on commit failure
            await self._session.rollback()
            raise RepositoryError(
                message=f"Failed to commit transaction: {str(e)}",
                operation="commit",
                entity_type="UnitOfWork",
                original_exception=e
            )
    
    async def rollback(self) -> None:
        """
        Rollback the transaction.
        
        Discards all changes made through repositories.
        
        Raises:
            RuntimeError: If called outside active context
        
        Note: Safe to call multiple times (idempotent)
        """
        if not self._is_active:
            raise RuntimeError(
                "Cannot rollback outside active UnitOfWork context. "
                "Use 'async with uow:' to activate."
            )
        
        await self._session.rollback()
    
    async def __aenter__(self) -> 'UnitOfWork':
        """
        Enter async context - begin transaction.
        
        Opens database session and marks UoW as active.
        
        Returns:
            UnitOfWork: Self, for use in 'async with' statement
        
        Raises:
            RuntimeError: If already active (no nested UoW)
        """
        if self._is_active:
            raise RuntimeError(
                "UnitOfWork is already active. Nested UnitOfWork not supported."
            )
        
        # Open session (begins transaction)
        self._session = await self._session_manager.get_session().__aenter__()
        self._is_active = True
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context - cleanup.
        
        Handles automatic rollback and resource cleanup:
        - If exception occurred: Rollback
        - If no explicit commit: Rollback (safe default)
        - Always: Close session and reset state
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        
        Design Decision: Why rollback if no commit?
        - Prevents accidental commits
        - Makes commit() explicit requirement
        - Safe default (fail closed)
        
        Note: Session close is idempotent (safe to call multiple times)
        """
        if not self._is_active:
            return  # Already cleaned up
        
        try:
            # Auto-rollback on exception or if no explicit commit
            # Session tracks if commit was called, but we rollback anyway
            # to be explicit and handle any uncommitted state
            if exc_type is not None:
                # Exception occurred - definitely rollback
                await self._session.rollback()
            else:
                # No exception, but rollback any uncommitted state
                # (commit() should have been called explicitly)
                try:
                    await self._session.rollback()
                except Exception:
                    # Rollback can fail if commit was called (that's ok)
                    pass
        finally:
            # Always cleanup state
            if self._session:
                await self._session.close()
            
            self._session = None
            self._is_active = False
            
            # Clear lazy-loaded repositories
            # (new UoW needs fresh repo instances)
            self._fermentation_repo = None
            self._sample_repo = None
