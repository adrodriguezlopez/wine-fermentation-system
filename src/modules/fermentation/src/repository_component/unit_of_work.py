"""
Unit of Work implementation for transactional repository coordination.

Concrete implementation of IUnitOfWork interface providing atomic
multi-repository operations under single database transaction.

Architecture: Repository Component Layer (Infrastructure)

Related ADRs:
- ADR-002: Repository Architecture (specifies UoW pattern)
- ADR-003: Error Handling Architecture
- ADR-031: Cross-Module Transaction Coordination (refactored to facade pattern)

Design Pattern: Facade + Unit of Work

Architectural Evolution (ADR-031):
This UnitOfWork has been refactored from a transaction manager to a facade
for repository access. Transaction lifecycle is now managed by TransactionScope
to enable cross-module coordination.

Key Changes:
- Transaction management: Moved to TransactionScope
- Context manager: Removed (__aenter__/__aexit__)
- Repository access: Remains lazy-loaded facade
- Session lifecycle: Managed by TransactionScope via ISessionManager
"""

from typing import Optional

from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.repositories.lot_source_repository_interface import ILotSourceRepository
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fruit_origin.src.domain.repositories.vineyard_block_repository_interface import IVineyardBlockRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.repository_component.repositories.lot_source_repository import LotSourceRepository
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_block_repository import VineyardBlockRepository
from src.shared.infra.interfaces.session_manager import ISessionManager


class UnitOfWork(IUnitOfWork):
    """
    Unit of Work facade for repository access.
    
    Provides lazy-loaded repositories that share a common session manager.
    Transaction lifecycle is managed externally by TransactionScope (ADR-031).
    
    Architectural Pattern (Post-ADR-031):
        Before: UnitOfWork managed transactions internally (context manager)
        After: UnitOfWork is a facade for repository access only
        
        Transaction management moved to TransactionScope to enable cross-module
        coordination (fermentation + fruit_origin operations in same transaction).
    
    Usage Patterns:
    
        Pattern 1 - With TransactionScope (Recommended):
        ```python
        async with TransactionScope(session_manager):
            fermentation = await uow.fermentation_repo.create(...)
            sample = await uow.sample_repo.create_sample(...)
            # Automatic commit on scope exit
        ```
        
        Pattern 2 - Direct Repository Access:
        ```python
        # For read-only or when transaction managed elsewhere
        fermentation = await uow.fermentation_repo.get_by_id(1)
        ```
        
        Pattern 3 - Manual Transaction Control:
        ```python
        await session_manager.begin()
        try:
            await uow.fermentation_repo.create(...)
            await session_manager.commit()
        except Exception:
            await session_manager.rollback()
            raise
        ```
    
    Thread Safety: NOT thread-safe (sessions are not thread-safe)
    Concurrency: Safe for asyncio (async/await)
    
    Design Decisions:
    - Lazy Repository Loading: Repos created only when accessed
    - Shared Session: All repos use same session manager
    - No Transaction Management: Delegated to TransactionScope
    - Facade Pattern: Simplified access to related repositories
    
    Backward Compatibility Note:
    Code using `async with uow:` needs refactoring to use TransactionScope.
    See ADR-031 migration guide for detailed upgrade path.
    """
    
    def __init__(self, session_manager: ISessionManager):
        """
        Initialize Unit of Work with session manager.
        
        Args:
            session_manager: Manages database sessions and transactions
        
        Note: Session manager is shared across all repositories
              created by this UnitOfWork.
        """
        self._session_manager = session_manager
        
        # Lazy-loaded repositories
        self._fermentation_repo: Optional[IFermentationRepository] = None
        self._sample_repo: Optional[ISampleRepository] = None
        self._lot_source_repo: Optional[ILotSourceRepository] = None
        self._harvest_lot_repo: Optional[IHarvestLotRepository] = None
        self._vineyard_repo: Optional[IVineyardRepository] = None
        self._vineyard_block_repo: Optional[IVineyardBlockRepository] = None
    
    @property
    def fermentation_repo(self) -> IFermentationRepository:
        """
        Get fermentation repository using shared session manager.
        
        Returns:
            IFermentationRepository: Repository with shared session
        
        Note: Lazy-loaded on first access. Repository uses session manager
              provided to UnitOfWork constructor.
        """
        if self._fermentation_repo is None:
            self._fermentation_repo = FermentationRepository(self._session_manager)
        
        return self._fermentation_repo
    
    @property
    def sample_repo(self) -> ISampleRepository:
        """
        Get sample repository using shared session manager.
        
        Returns:
            ISampleRepository: Repository with shared session
        
        Note: Lazy-loaded on first access.
        """
        if self._sample_repo is None:
            self._sample_repo = SampleRepository(self._session_manager)
        
        return self._sample_repo
    
    @property
    def lot_source_repo(self) -> ILotSourceRepository:
        """
        Get lot source repository using shared session manager.
        
        Returns:
            ILotSourceRepository: Repository with shared session
        
        Note: Lazy-loaded on first access.
        """
        if self._lot_source_repo is None:
            self._lot_source_repo = LotSourceRepository(self._session_manager)
        
        return self._lot_source_repo
    
    @property
    def harvest_lot_repo(self) -> IHarvestLotRepository:
        """
        Get harvest lot repository using shared session manager.
        
        Returns:
            IHarvestLotRepository: Repository with shared session
        
        Note: Lazy-loaded on first access.
        """
        if self._harvest_lot_repo is None:
            self._harvest_lot_repo = HarvestLotRepository(self._session_manager)
        
        return self._harvest_lot_repo
    
    @property
    def vineyard_repo(self) -> IVineyardRepository:
        """
        Get vineyard repository using shared session manager.
        
        Returns:
            IVineyardRepository: Repository with shared session
        
        Note: Lazy-loaded on first access.
        """
        if self._vineyard_repo is None:
            self._vineyard_repo = VineyardRepository(self._session_manager)
        
        return self._vineyard_repo
    
    @property
    def vineyard_block_repo(self) -> IVineyardBlockRepository:
        """
        Get vineyard block repository using shared session manager.
        
        Returns:
            IVineyardBlockRepository: Repository with shared session
        
        Note: Lazy-loaded on first access.
        """
        if self._vineyard_block_repo is None:
            self._vineyard_block_repo = VineyardBlockRepository(self._session_manager)
        
        return self._vineyard_block_repo
