"""
Interface definition for Fruit Origin Service.

Service layer for vineyard and harvest lot business logic orchestration.
Coordinates validation, repository access, and business rules.

Follows Clean Architecture principles:
- Uses DTOs from domain layer (VineyardCreate, HarvestLotCreate)
- Returns ORM entities (Vineyard, HarvestLot)
- Delegates data access to repositories
- Does NOT handle authentication (API layer responsibility)

Related ADRs:
- ADR-001: Fruit Origin Model (domain entities)
- ADR-002: Repository Architecture (data access layer)
- ADR-014: Fruit Origin Service Layer (this service)
- ADR-025: Multi-Tenancy Security (winery_id enforcement)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (observability)
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import VineyardCreate, VineyardUpdate
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate, HarvestLotUpdate


class IFruitOriginService(ABC):
    """
    Interface for fruit origin management service.
    
    Orchestrates:
    - Vineyard lifecycle (CRUD with business rules)
    - Harvest lot lifecycle (creation with validation)
    - Business rule enforcement
    
    Does NOT handle:
    - Authentication (API layer responsibility)
    - Direct database access (uses repositories)
    - Grape variety catalog (separate concern - global data)
    
    Design Philosophy:
    - Unified service for cohesive bounded context (Fruit Origin domain)
    - Follows Fermentation Service pattern (ADR-005)
    - Security-first (ADR-025 integrated from day 1)
    - Observable (ADR-027 structured logging)
    """
    
    # ==================================================================================
    # VINEYARD OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def create_vineyard(
        self,
        winery_id: int,
        user_id: int,
        data: VineyardCreate
    ) -> Vineyard:
        """
        Create a new vineyard with validation.
        
        Business logic:
        1. Validates vineyard data (code format)
        2. Creates vineyard record (uniqueness enforced by DB)
        3. Records audit trail
        
        Args:
            winery_id: Owner winery ID (multi-tenant scoping)
            user_id: User creating vineyard (audit trail)
            data: Vineyard creation data
            
        Returns:
            Created vineyard entity
            
        Raises:
            DuplicateCodeError: Code already exists for this winery (ADR-026)
            RepositoryError: Database error (ADR-026)
        """
        pass
    
    @abstractmethod
    async def get_vineyard(
        self,
        vineyard_id: int,
        winery_id: int
    ) -> Optional[Vineyard]:
        """
        Get vineyard by ID with access control.
        
        Security:
        - Returns vineyard ONLY if belongs to winery_id (ADR-025)
        - Returns None if not found or access denied
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            
        Returns:
            Vineyard if found and accessible, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_vineyards(
        self,
        winery_id: int,
        include_deleted: bool = False
    ) -> List[Vineyard]:
        """
        List all vineyards for a winery.
        
        Args:
            winery_id: Winery ID (multi-tenant filter)
            include_deleted: Include soft-deleted vineyards
            
        Returns:
            List of vineyards (may be empty)
        """
        pass
    
    @abstractmethod
    async def update_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int,
        data: VineyardUpdate
    ) -> Vineyard:
        """
        Update vineyard details.
        
        Security:
        - Only updates if vineyard belongs to winery_id (ADR-025)
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            user_id: User updating (audit trail)
            data: Update data (only provided fields updated)
            
        Returns:
            Updated vineyard
            
        Raises:
            VineyardNotFound: Vineyard doesn't exist or access denied (ADR-026)
            DuplicateCodeError: Code already exists for this winery (ADR-026)
        """
        pass
    
    @abstractmethod
    async def delete_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete a vineyard with cascade validation.
        
        Business rule (ADR-014):
        - Cannot delete vineyard if it has active (non-deleted) harvest lots
        
        Security:
        - Only deletes if vineyard belongs to winery_id (ADR-025)
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            user_id: User deleting (audit trail)
            
        Returns:
            True if deleted successfully
            
        Raises:
            VineyardNotFound: Vineyard doesn't exist or access denied (ADR-026)
            VineyardHasActiveLotsError: Cannot delete - has active lots (ADR-026)
        """
        pass
    
    # ==================================================================================
    # HARVEST LOT OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def create_harvest_lot(
        self,
        winery_id: int,
        user_id: int,
        data: HarvestLotCreate
    ) -> HarvestLot:
        """
        Create harvest lot with full validation.
        
        Business logic (ADR-014):
        1. Validates harvest date (cannot be in future - data quality)
        2. Validates vineyard block exists (can be from different winery - buying grapes)
        3. Creates harvest lot record
        
        MVP Simplification (ADR-014):
        - No mass total validation (deferred)
        - Grape composition handled by existing HarvestLotCreate DTO
        
        Security:
        - Harvest lot belongs to winery_id (ADR-025)
        - Vineyard block can be from different winery (cross-winery purchase allowed)
        
        Args:
            winery_id: Winery harvesting grapes (owner of this lot)
            user_id: User creating lot (audit trail)
            data: Harvest lot creation data
            
        Returns:
            Created harvest lot
            
        Raises:
            InvalidHarvestDate: Harvest date in future (ADR-026)
            VineyardBlockNotFound: Block doesn't exist (ADR-026)
            DuplicateCodeError: Code already exists for this winery (ADR-026)
        """
        pass
    
    @abstractmethod
    async def get_harvest_lot(
        self,
        lot_id: int,
        winery_id: int
    ) -> Optional[HarvestLot]:
        """
        Get harvest lot by ID with access control.
        
        Security:
        - Returns lot ONLY if belongs to winery_id (ADR-025)
        - Returns None if not found or access denied
        
        Args:
            lot_id: Harvest lot ID
            winery_id: Winery ID for access control
            
        Returns:
            Harvest lot if found and accessible, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_harvest_lots(
        self,
        winery_id: int,
        vineyard_id: Optional[int] = None
    ) -> List[HarvestLot]:
        """
        List harvest lots for a winery, optionally filtered by vineyard.
        
        Args:
            winery_id: Winery ID (multi-tenant filter)
            vineyard_id: Optional vineyard filter
            
        Returns:
            List of harvest lots (may be empty)
        """
        pass
    
    @abstractmethod
    async def update_harvest_lot(
        self,
        lot_id: int,
        winery_id: int,
        user_id: int,
        data: "HarvestLotUpdate"
    ) -> HarvestLot:
        """
        Update harvest lot details.
        
        Security:
        - Only updates if lot belongs to winery_id (ADR-025)
        
        Args:
            lot_id: Harvest lot ID
            winery_id: Winery ID for access control
            user_id: User updating (audit trail)
            data: Update data (only provided fields updated)
            
        Returns:
            Updated harvest lot
            
        Raises:
            HarvestLotNotFound: Lot doesn't exist or access denied (ADR-026)
            DuplicateCodeError: Code already exists for this winery (ADR-026)
        """
        pass
    
    @abstractmethod
    async def delete_harvest_lot(
        self,
        lot_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete a harvest lot with validation.
        
        Business rule (ADR-014):
        - Cannot delete lot if used in any fermentation (active or completed)
        
        Security:
        - Only deletes if lot belongs to winery_id (ADR-025)
        
        Args:
            lot_id: Harvest lot ID
            winery_id: Winery ID for access control
            user_id: User deleting (audit trail)
            
        Returns:
            True if deleted successfully
            
        Raises:
            HarvestLotNotFound: Lot doesn't exist or access denied (ADR-026)
            HarvestLotInUseError: Cannot delete - used in fermentation (ADR-026)
        """
        pass
