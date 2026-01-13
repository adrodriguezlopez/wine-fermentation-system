"""
TransactionScope - Coordinates transaction lifecycle across multiple services.

Architecture: Infrastructure Layer (Session Management)
Pattern: Context Manager for Transaction Coordination
ADR: ADR-031 Cross-Module Transaction Coordination

Related Components:
- ISessionManager: Interface for session/transaction management
- UnitOfWork: Facade for repository access
- ETLService: Primary consumer for cross-module operations

Design Pattern: Unit of Work + Coordinator
- Manages transaction begin/commit/rollback lifecycle
- Coordinates multiple services in single atomic operation
- Automatic rollback on exception

Usage:
    ```python
    async with TransactionScope(session_manager):
        # All operations within scope share same transaction
        harvest_lot = await fruit_origin_service.ensure_harvest_lot(...)
        fermentation = await fermentation_repo.create(...)
        # Automatic commit on success, rollback on exception
    ```
"""

from typing import Optional
from src.shared.infra.interfaces.session_manager import ISessionManager
import structlog

logger = structlog.get_logger(__name__)


class TransactionScope:
    """
    Context manager for coordinating transactions across multiple services.
    
    Ensures all operations within the scope participate in the same transaction,
    with automatic commit on success and rollback on exception.
    
    Key Features:
    - Atomic operations: All succeed or all rollback
    - Cross-module coordination: Multiple services share transaction
    - Exception safety: Automatic rollback on any error
    - Module independence: Services remain decoupled via ISessionManager
    
    Design Principles:
    - Single Responsibility: Transaction lifecycle only
    - Dependency Inversion: Depends on ISessionManager interface
    - Open/Closed: Extensible to new services without modification
    
    Example:
        ```python
        # ETL Service coordinating fruit origin + fermentation
        for fermentation_data in fermentations:
            try:
                async with TransactionScope(self._session_manager):
                    # Fruit origin operations (cross-module)
                    harvest_lot = await self._fruit_origin_service.ensure_harvest_lot(...)
                    
                    # Fermentation operations (same transaction)
                    fermentation = await self._fermentation_repo.create(...)
                    
                    # Automatic commit on scope exit
                    
            except Exception as e:
                # Automatic rollback already happened
                logger.error("fermentation_import_failed", error=str(e))
        ```
    
    Thread Safety: Not thread-safe - designed for async single-threaded use
    """
    
    def __init__(self, session_manager: ISessionManager):
        """
        Initialize transaction scope with session manager.
        
        Args:
            session_manager: Session manager implementing transaction methods
                           (begin, commit, rollback)
        
        Design Note: Accepts interface, not concrete implementation, following
        Dependency Inversion Principle (SOLID).
        """
        self._session_manager = session_manager
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self) -> "TransactionScope":
        """
        Enter transaction scope - begin transaction.
        
        Returns:
            TransactionScope: Self for context manager protocol
        
        Note: Some session manager implementations (like SharedSessionManager)
        may no-op if transaction already active.
        """
        await self._session_manager.begin()
        logger.debug("transaction_scope_entered")
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[object]
    ) -> bool:
        """
        Exit transaction scope - commit or rollback.
        
        Args:
            exc_type: Exception type if exception occurred, None otherwise
            exc_val: Exception value if exception occurred
            exc_tb: Exception traceback
        
        Returns:
            bool: Always False (exceptions not suppressed)
        
        Behavior:
        - No exception: Commit transaction
        - Exception raised: Rollback transaction
        - Exception propagates after rollback
        
        Design Rationale:
        - Explicit is better than implicit (Python Zen)
        - Caller should handle exceptions, not TransactionScope
        - Rollback ensures database consistency on failure
        """
        if exc_type is None:
            # Success path: commit transaction
            await self._session_manager.commit()
            self._committed = True
            logger.debug("transaction_scope_committed")
        else:
            # Error path: rollback transaction
            await self._session_manager.rollback()
            self._rolled_back = True
            logger.warning(
                "transaction_scope_rolled_back",
                exception_type=exc_type.__name__,
                exception_message=str(exc_val)
            )
        
        # Always return False to propagate exceptions
        return False
    
    @property
    def committed(self) -> bool:
        """
        Check if transaction was committed.
        
        Returns:
            bool: True if commit() was called, False otherwise
        
        Usage: Primarily for testing and debugging
        """
        return self._committed
    
    @property
    def rolled_back(self) -> bool:
        """
        Check if transaction was rolled back.
        
        Returns:
            bool: True if rollback() was called, False otherwise
        
        Usage: Primarily for testing and debugging
        """
        return self._rolled_back
