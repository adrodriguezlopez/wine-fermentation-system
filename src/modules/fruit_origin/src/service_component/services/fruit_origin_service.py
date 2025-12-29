"""
Fruit Origin Service Implementation.

Orchestrates business logic for vineyard and harvest lot management.
Integrates security (ADR-025), error handling (ADR-026), and logging (ADR-027).

Related ADRs:
- ADR-001: Fruit Origin Model (domain entities)
- ADR-002: Repository Architecture (data access)
- ADR-014: Fruit Origin Service Layer (this service)
- ADR-025: Multi-Tenancy Security (winery_id enforcement)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (observability)
"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

# Service interface
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import (
    IFruitOriginService,
)

# Domain entities
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot

# DTOs
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate, HarvestLotUpdate

# Repositories
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import (
    IVineyardRepository,
)
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import (
    IHarvestLotRepository,
)

# Errors (ADR-026)
from src.shared.domain.errors import (
    VineyardNotFound,
    VineyardHasActiveLotsError,
    VineyardBlockNotFound,
    InvalidHarvestDate,
    HarvestLotNotFound,
    DuplicateCodeError,
)

logger = get_logger(__name__)


class FruitOriginService(IFruitOriginService):
    """
    Service for managing fruit origin operations.
    
    Responsibilities:
    - Orchestrate vineyard and harvest lot operations
    - Enforce business rules (harvest dates, cascade deletes)
    - Coordinate multiple repositories
    - Integrate security (ADR-025) and logging (ADR-027)
    
    Design:
    - Depends on abstractions (repositories via DI)
    - Returns domain entities
    - Uses DTOs for input validation
    """
    
    def __init__(
        self,
        vineyard_repo: IVineyardRepository,
        harvest_lot_repo: IHarvestLotRepository,
    ):
        """
        Initialize service with dependencies (Dependency Injection).
        
        Args:
            vineyard_repo: Repository for vineyard data
            harvest_lot_repo: Repository for harvest lot data
        """
        self._vineyard_repo = vineyard_repo
        self._harvest_lot_repo = harvest_lot_repo
    
    # ==================================================================================
    # VINEYARD OPERATIONS
    # ==================================================================================
    
    async def create_vineyard(
        self,
        winery_id: int,
        user_id: int,
        data: VineyardCreate
    ) -> Vineyard:
        """Create vineyard with validation."""
        with LogTimer(logger, "create_vineyard_service"):
            logger.info(
                "creating_vineyard",
                winery_id=winery_id,
                user_id=user_id,
                code=data.code,
                name=data.name
            )
            
            # Delegate to repository (handles uniqueness constraint via DB)
            vineyard = await self._vineyard_repo.create(
                winery_id=winery_id,
                data=data
            )
            
            logger.info(
                "vineyard_created_success",
                vineyard_id=vineyard.id,
                winery_id=winery_id,
                code=vineyard.code,
                user_id=user_id
            )
            
            return vineyard
    
    async def get_vineyard(
        self,
        vineyard_id: int,
        winery_id: int
    ) -> Optional[Vineyard]:
        """Get vineyard by ID with access control."""
        with LogTimer(logger, "get_vineyard_service"):
            logger.info(
                "getting_vineyard",
                vineyard_id=vineyard_id,
                winery_id=winery_id
            )
            
            vineyard = await self._vineyard_repo.get_by_id(
                vineyard_id=vineyard_id,
                winery_id=winery_id
            )
            
            if vineyard:
                logger.info(
                    "vineyard_found",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id,
                    code=vineyard.code
                )
            else:
                logger.info(
                    "vineyard_not_found",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id
                )
            
            return vineyard
    
    async def list_vineyards(
        self,
        winery_id: int,
        include_deleted: bool = False
    ) -> List[Vineyard]:
        """List all vineyards for a winery."""
        with LogTimer(logger, "list_vineyards_service"):
            logger.info(
                "listing_vineyards",
                winery_id=winery_id,
                include_deleted=include_deleted
            )
            
            vineyards = await self._vineyard_repo.get_by_winery(winery_id=winery_id)
            
            # Filter out deleted if requested
            if not include_deleted:
                vineyards = [v for v in vineyards if not v.is_deleted]
            
            logger.info(
                "vineyards_listed",
                winery_id=winery_id,
                count=len(vineyards),
                include_deleted=include_deleted
            )
            
            return vineyards
    
    async def update_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int,
        data: VineyardUpdate
    ) -> Vineyard:
        """Update vineyard details."""
        with LogTimer(logger, "update_vineyard_service"):
            logger.info(
                "updating_vineyard",
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            # Update via repository
            vineyard = await self._vineyard_repo.update(
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                data=data
            )
            
            if not vineyard:
                logger.warning(
                    "vineyard_not_found_for_update",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id
                )
                raise VineyardNotFound(
                    f"Vineyard {vineyard_id} not found or access denied",
                    vineyard_id=vineyard_id
                )
            
            logger.info(
                "vineyard_updated_success",
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            return vineyard
    
    async def delete_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete vineyard with cascade validation.
        
        Business Rule: Cannot delete if has active harvest lots.
        """
        with LogTimer(logger, "delete_vineyard_service"):
            logger.info(
                "deleting_vineyard",
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            # Check if vineyard exists
            vineyard = await self._vineyard_repo.get_by_id(vineyard_id, winery_id)
            if not vineyard:
                logger.warning(
                    "vineyard_not_found_for_delete",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id
                )
                raise VineyardNotFound(
                    f"Vineyard {vineyard_id} not found or access denied",
                    vineyard_id=vineyard_id
                )
            
            # Check for active harvest lots (via vineyard blocks)
            # Query blocks directly instead of using lazy loading
            session_cm = await self._vineyard_repo.get_session()
            async with session_cm as session:
                # Get all block IDs for this vineyard
                block_query = select(VineyardBlock.id).where(
                    VineyardBlock.vineyard_id == vineyard_id,
                    VineyardBlock.is_deleted == False
                )
                block_result = await session.execute(block_query)
                all_blocks_ids = [row[0] for row in block_result.fetchall()]
            
            # Count active lots across all blocks
            active_lots_count = 0
            for block_id in all_blocks_ids:
                lots = await self._harvest_lot_repo.get_by_block(block_id, winery_id)
                # Count non-deleted lots
                active_lots_count += sum(1 for lot in lots if not lot.is_deleted)
            
            if active_lots_count > 0:
                logger.warning(
                    "vineyard_delete_blocked_has_active_lots",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id,
                    active_lots_count=active_lots_count
                )
                raise VineyardHasActiveLotsError(
                    f"Cannot delete vineyard {vineyard_id}: has {active_lots_count} active harvest lots",
                    vineyard_id=vineyard_id,
                    active_lots_count=active_lots_count
                )
            
            # Soft delete
            success = await self._vineyard_repo.delete(vineyard_id, winery_id)
            
            if success:
                logger.info(
                    "vineyard_deleted_success",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id,
                    user_id=user_id
                )
            else:
                logger.warning(
                    "vineyard_delete_failed",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id
                )
            
            return success
    
    # ==================================================================================
    # HARVEST LOT OPERATIONS
    # ==================================================================================
    
    async def create_harvest_lot(
        self,
        winery_id: int,
        user_id: int,
        data: HarvestLotCreate
    ) -> HarvestLot:
        """
        Create harvest lot with validation.
        
        Business Rules:
        1. Harvest date cannot be in future (data quality)
        2. Vineyard block must exist (can be from different winery - buying grapes)
        """
        with LogTimer(logger, "create_harvest_lot_service"):
            logger.info(
                "creating_harvest_lot",
                winery_id=winery_id,
                user_id=user_id,
                code=data.code,
                block_id=data.block_id,
                harvest_date=data.harvest_date.isoformat()
            )
            
            # Validation 1: Harvest date not in future
            # Convert date to datetime at start of day for comparison
            harvest_datetime = datetime.combine(data.harvest_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            
            if harvest_datetime > now:
                logger.warning(
                    "harvest_date_in_future_rejected",
                    harvest_date=data.harvest_date.isoformat(),
                    winery_id=winery_id,
                    user_id=user_id
                )
                raise InvalidHarvestDate(
                    f"Harvest date {data.harvest_date} cannot be in the future",
                    harvest_date=data.harvest_date
                )
            
            # Note: Vineyard block existence validation is handled by repository layer
            # (foreign key constraint will catch invalid block_id)
            
            # Create harvest lot via repository
            try:
                harvest_lot = await self._harvest_lot_repo.create(
                    winery_id=winery_id,
                    data=data
                )
                
                logger.info(
                    "harvest_lot_created_success",
                    lot_id=harvest_lot.id,
                    winery_id=winery_id,
                    code=harvest_lot.code,
                    user_id=user_id
                )
                
                return harvest_lot
            
            except Exception as e:
                # Check if it's a foreign key constraint error (block not found)
                error_str = str(e).lower()
                if "foreign key" in error_str and "block" in error_str:
                    logger.warning(
                        "vineyard_block_not_found",
                        block_id=data.block_id,
                        winery_id=winery_id
                    )
                    raise VineyardBlockNotFound(
                        f"Vineyard block {data.block_id} not found",
                        block_id=data.block_id
                    ) from e
                # Re-raise other errors
                raise
    
    async def get_harvest_lot(
        self,
        lot_id: int,
        winery_id: int
    ) -> Optional[HarvestLot]:
        """Get harvest lot by ID with access control."""
        with LogTimer(logger, "get_harvest_lot_service"):
            logger.info(
                "getting_harvest_lot",
                lot_id=lot_id,
                winery_id=winery_id
            )
            
            harvest_lot = await self._harvest_lot_repo.get_by_id(
                lot_id=lot_id,
                winery_id=winery_id
            )
            
            if harvest_lot:
                logger.info(
                    "harvest_lot_found",
                    lot_id=lot_id,
                    winery_id=winery_id,
                    code=harvest_lot.code
                )
            else:
                logger.info(
                    "harvest_lot_not_found",
                    lot_id=lot_id,
                    winery_id=winery_id
                )
            
            return harvest_lot
    
    async def list_harvest_lots(
        self,
        winery_id: int,
        vineyard_id: Optional[int] = None
    ) -> List[HarvestLot]:
        """List harvest lots for a winery, optionally filtered by vineyard."""
        with LogTimer(logger, "list_harvest_lots_service"):
            logger.info(
                "listing_harvest_lots",
                winery_id=winery_id,
                vineyard_id=vineyard_id
            )
            
            if vineyard_id:
                # Get vineyard to get all its blocks
                vineyard = await self._vineyard_repo.get_by_id(vineyard_id, winery_id)
                if not vineyard:
                    logger.warning(
                        "vineyard_not_found_for_harvest_lots_list",
                        vineyard_id=vineyard_id,
                        winery_id=winery_id
                    )
                    return []
                
                # Get lots for all blocks in this vineyard
                all_lots = []
                for block in vineyard.blocks:
                    lots = await self._harvest_lot_repo.get_by_block(block.id, winery_id)
                    all_lots.extend(lots)
                
                logger.info(
                    "harvest_lots_listed_by_vineyard",
                    winery_id=winery_id,
                    vineyard_id=vineyard_id,
                    count=len(all_lots)
                )
                
                return all_lots
            else:
                # Get all lots for winery
                lots = await self._harvest_lot_repo.get_by_winery(winery_id)
                
                logger.info(
                    "harvest_lots_listed",
                    winery_id=winery_id,
                    count=len(lots)
                )
                
                return lots
    
    async def update_harvest_lot(
        self,
        lot_id: int,
        winery_id: int,
        user_id: int,
        data: HarvestLotUpdate
    ) -> HarvestLot:
        """Update harvest lot with validation."""
        with LogTimer(logger, "update_harvest_lot_service"):
            logger.info(
                "updating_harvest_lot",
                lot_id=lot_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            # Get existing lot with access control
            existing_lot = await self._harvest_lot_repo.get_by_id(lot_id, winery_id)
            if not existing_lot:
                logger.warning(
                    "harvest_lot_not_found_for_update",
                    lot_id=lot_id,
                    winery_id=winery_id
                )
                raise HarvestLotNotFound(lot_id)
            
            # Check for code uniqueness if code is being changed
            if data.code and data.code != existing_lot.code:
                existing_by_code = await self._harvest_lot_repo.get_by_code(data.code, winery_id)
                if existing_by_code:
                    logger.warning(
                        "duplicate_harvest_lot_code_on_update",
                        code=data.code,
                        winery_id=winery_id,
                        existing_lot_id=existing_by_code.id
                    )
                    raise DuplicateCodeError(f"Harvest lot code '{data.code}' already exists")
            
            # Update lot
            updated_lot = await self._harvest_lot_repo.update(lot_id, winery_id, data)
            
            logger.info(
                "harvest_lot_updated",
                lot_id=lot_id,
                lot_code=updated_lot.code,
                winery_id=winery_id
            )
            
            return updated_lot
    
    async def delete_harvest_lot(
        self,
        lot_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """Soft delete harvest lot with usage validation."""
        with LogTimer(logger, "delete_harvest_lot_service"):
            logger.info(
                "deleting_harvest_lot",
                lot_id=lot_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            # Get existing lot with access control
            existing_lot = await self._harvest_lot_repo.get_by_id(lot_id, winery_id)
            if not existing_lot:
                logger.warning(
                    "harvest_lot_not_found_for_delete",
                    lot_id=lot_id,
                    winery_id=winery_id
                )
                raise HarvestLotNotFound(lot_id)
            
            # TODO Phase 3: Check if lot is used in any fermentation
            # This requires integration with fermentation module
            # For now, we allow deletion (will be blocked by foreign key constraint if used)
            
            # Soft delete
            success = await self._harvest_lot_repo.delete(lot_id, winery_id)
            
            if success:
                logger.info(
                    "harvest_lot_deleted",
                    lot_id=lot_id,
                    lot_code=existing_lot.code,
                    winery_id=winery_id
                )
            else:
                logger.error(
                    "harvest_lot_delete_failed",
                    lot_id=lot_id,
                    winery_id=winery_id
                )
            
            return success
