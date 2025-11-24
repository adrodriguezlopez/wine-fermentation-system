"""
Unit of Work interface for transaction management.

Provides coordinated access to multiple repositories within a single
database transaction, ensuring atomicity of operations.

Design Pattern: Unit of Work (Martin Fowler, Patterns of Enterprise Application Architecture)
Architecture: Clean Architecture - Domain Layer (Interfaces)

Related ADRs:
- ADR-002: Repository Architecture
- ADR-005: Service Layer Interfaces & Type Safety
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
    from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
    from src.modules.fermentation.src.domain.repositories.lot_source_repository_interface import ILotSourceRepository


class IUnitOfWork(ABC):
    """
    Unit of Work pattern for managing transactional boundaries.
    
    Coordinates access to multiple repositories within a single database
    transaction. Ensures that all changes are committed or rolled back together,
    maintaining data consistency.
    
    Usage:
        ```python
        async with uow:
            # All operations share same transaction
            fermentation = await uow.fermentation_repo.create(...)
            sample = await uow.sample_repo.create_sample(...)
            
            # Commit all changes atomically
            await uow.commit()
        ```
    
    Design Principles:
    - Transaction Atomicity: All or nothing
    - Repository Coordination: Multiple repos, one transaction
    - Explicit Commit: Requires explicit commit() call
    - Auto Rollback: Automatic rollback on exception
    - Context Manager: Pythonic resource management
    
    Responsibilities:
    - Manage transaction lifecycle (begin, commit, rollback)
    - Provide access to repositories with shared session
    - Ensure atomicity of multi-repository operations
    - Handle cleanup on context exit
    
    Note: This is an abstract interface. Concrete implementation
    is in repository_component layer (infrastructure concern).
    """
    
    @property
    @abstractmethod
    def fermentation_repo(self) -> 'IFermentationRepository':
        """
        Access to fermentation repository within this UoW.
        
        Returns:
            IFermentationRepository: Repository sharing UoW's transaction
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def sample_repo(self) -> 'ISampleRepository':
        """
        Access to sample repository within this UoW.
        
        Returns:
            ISampleRepository: Repository sharing UoW's transaction
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def lot_source_repo(self) -> 'ILotSourceRepository':
        """
        Access to lot source repository within this UoW.
        
        Returns:
            ILotSourceRepository: Repository sharing UoW's transaction
        
        Raises:
            RuntimeError: If accessed outside active context
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @abstractmethod
    async def commit(self) -> None:
        """
        Commit the transaction.
        
        Persists all changes made through repositories to the database.
        After commit, the transaction is complete and context should exit.
        
        Raises:
            RuntimeError: If called outside active context
            RepositoryError: If commit fails (database error)
        
        Note: On commit failure, automatic rollback is triggered.
        
        Example:
            ```python
            async with uow:
                await uow.fermentation_repo.create(...)
                await uow.sample_repo.create_sample(...)
                await uow.commit()  # All changes persisted
            ```
        """
        ...
    
    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback the transaction.
        
        Discards all changes made through repositories.
        Database state is restored to before transaction began.
        
        Raises:
            RuntimeError: If called outside active context
        
        Note: Usually not called explicitly - context manager
        handles automatic rollback on exception.
        
        Example:
            ```python
            async with uow:
                await uow.fermentation_repo.create(...)
                if some_condition:
                    await uow.rollback()  # Explicit rollback
                    return
                await uow.commit()
            ```
        """
        ...
    
    @abstractmethod
    async def __aenter__(self) -> 'IUnitOfWork':
        """
        Enter async context - begin transaction.
        
        Opens database session and begins transaction.
        All repository operations will use this session.
        
        Returns:
            IUnitOfWork: Self, for use in 'async with' statement
        
        Example:
            ```python
            async with uow:  # <-- __aenter__ called here
                # Transaction active
                ...
            ```
        """
        ...
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context - cleanup.
        
        Automatically handles transaction completion:
        - If exception occurred: Rollback
        - If commit() not called: Rollback (safe default)
        - Always: Close session and cleanup state
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        
        Note: Automatic rollback on exception ensures data consistency.
        
        Example:
            ```python
            async with uow:
                ...
            # <-- __aexit__ called here (auto-rollback if no commit)
            ```
        """
        ...
