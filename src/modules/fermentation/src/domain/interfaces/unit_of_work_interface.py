"""
Unit of Work interface for repository access.

Provides unified access to multiple repositories across modules.
Acts as a facade pattern to simplify repository coordination.

Design Pattern: Facade (Gamma et al., Design Patterns)
Architecture: Clean Architecture - Domain Layer (Interfaces)

Related ADRs:
- ADR-002: Repository Architecture
- ADR-005: Service Layer Interfaces & Type Safety
- ADR-031: TransactionScope Migration (UnitOfWork refactored to facade)

Note: Transaction management is handled separately via TransactionScope.
UnitOfWork provides repository access only.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
    from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
    from src.modules.fermentation.src.domain.repositories.lot_source_repository_interface import ILotSourceRepository
    from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository
    from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
    from src.modules.fruit_origin.src.domain.repositories.vineyard_block_repository_interface import IVineyardBlockRepository


class IUnitOfWork(ABC):
    """
    Facade for unified repository access across modules.
    
    Provides centralized access to repositories from both fermentation
    and fruit_origin modules. All repositories share the same session manager,
    enabling coordinated operations within a transaction.
    
    Usage:
        ```python
        async with TransactionScope(session_manager) as scope:
            uow = UnitOfWork(session_manager)
            
            # Access repositories through facade
            fermentation = await uow.fermentation_repo.create(...)
            sample = await uow.sample_repo.create_sample(...)
            harvest_lot = await uow.harvest_lot_repo.create(...)
            
            # Transaction managed by TransactionScope
        ```
    
    Design Principles:
    - Facade Pattern: Simplifies repository access
    - Lazy Loading: Repositories initialized on first access
    - Session Sharing: All repos use same session manager
    - Cross-Module: Supports fermentation + fruit_origin repos
    
    Responsibilities:
    - Provide access to 6 repositories (3 fermentation, 3 fruit_origin)
    - Ensure all repositories share same session manager
    - Lazy-load repositories on demand
    - Simplify multi-repository operations
    
    Note: Transaction lifecycle (begin, commit, rollback) is managed
    by TransactionScope. UnitOfWork is purely for repository access.
    """
    
    @property
    @abstractmethod
    def fermentation_repo(self) -> 'IFermentationRepository':
        """
        Access to fermentation repository.
        
        Returns:
            IFermentationRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def sample_repo(self) -> 'ISampleRepository':
        """
        Access to sample repository.
        
        Returns:
            ISampleRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def lot_source_repo(self) -> 'ILotSourceRepository':
        """
        Access to lot source repository.
        
        Returns:
            ILotSourceRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def harvest_lot_repo(self) -> 'IHarvestLotRepository':
        """
        Access to harvest lot repository.
        
        Returns:
            IHarvestLotRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def vineyard_repo(self) -> 'IVineyardRepository':
        """
        Access to vineyard repository.
        
        Returns:
            IVineyardRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    
    @property
    @abstractmethod
    def vineyard_block_repo(self) -> 'IVineyardBlockRepository':
        """
        Access to vineyard block repository.
        
        Returns:
            IVineyardBlockRepository: Repository sharing UoW's session manager
        
        Note: Lazy-loaded on first access
        """
        ...
    

