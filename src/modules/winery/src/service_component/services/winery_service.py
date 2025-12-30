"""
Winery Service Implementation.

Orchestrates business logic for winery management.
Integrates security (ADR-025), error handling (ADR-026), and logging (ADR-027).

Related ADRs:
- ADR-009: Missing Repositories (WineryRepository complete)
- ADR-016: Winery Service Layer (this service)
- ADR-025: Multi-Tenancy Security (Winery is root entity)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (observability)
"""
from typing import List, Optional
import re

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

# Service interface
from src.modules.winery.src.service_component.interfaces.winery_service_interface import IWineryService

# Domain entities
from src.modules.winery.src.domain.entities.winery import Winery

# DTOs
from src.modules.winery.src.domain.dtos.winery_dtos import WineryCreate, WineryUpdate

# Repositories
from src.modules.winery.src.domain.repositories.winery_repository_interface import IWineryRepository

# Cross-module repositories (for deletion protection)
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository

# Errors (ADR-026)
from src.shared.domain.errors import (
    WineryNotFound,
    WineryHasActiveDataError,
    DuplicateCodeError,
    InvalidWineryData,
)

logger = get_logger(__name__)


class WineryService(IWineryService):
    """
    Service for managing winery operations.
    
    Responsibilities:
    - Orchestrate winery CRUD operations
    - Enforce business rules (global code uniqueness, required fields)
    - Validate deletion safety (check active data in other modules)
    - Integrate security (ADR-025) and logging (ADR-027)
    
    Design:
    - Depends on abstractions (repositories via DI)
    - Returns domain entities
    - Uses DTOs for input validation
    - Simple validation (no ValidationOrchestrator - YAGNI for single entity)
    """
    
    def __init__(
        self,
        winery_repo: IWineryRepository,
        vineyard_repo: IVineyardRepository,
        fermentation_repo: IFermentationRepository,
    ):
        """
        Initialize service with dependencies (Dependency Injection).
        
        Args:
            winery_repo: Repository for winery data
            vineyard_repo: Repository for vineyard data (cross-module for deletion check)
            fermentation_repo: Repository for fermentation data (cross-module for deletion check)
        """
        self._winery_repo = winery_repo
        self._vineyard_repo = vineyard_repo
        self._fermentation_repo = fermentation_repo
    
    # ==================================================================================
    # CREATE OPERATIONS
    # ==================================================================================
    
    async def create_winery(
        self,
        data: WineryCreate
    ) -> Winery:
        """Create winery with validation."""
        with LogTimer(logger, "create_winery_service"):
            logger.info(
                "creating_winery",
                code=data.code,
                name=data.name
            )
            
            # Validate required fields
            if not data.code or not data.code.strip():
                logger.warning("winery_validation_failed", error="Code is required")
                raise InvalidWineryData("Code is required", field="code")
            
            if not data.name or not data.name.strip():
                logger.warning("winery_validation_failed", error="Name is required")
                raise InvalidWineryData("Name is required", field="name")
            
            # Validate code format (uppercase alphanumeric + hyphens)
            if not re.match(r'^[A-Z0-9-]+$', data.code):
                logger.warning(
                    "winery_validation_failed",
                    code=data.code,
                    error="Code must be uppercase alphanumeric with hyphens only"
                )
                raise InvalidWineryData(
                    "Code must be uppercase alphanumeric with hyphens only (e.g., 'BODEGA-001')",
                    field="code",
                    value=data.code
                )
            
            # Check code uniqueness (global across all wineries)
            existing = await self._winery_repo.get_by_code(data.code)
            if existing:
                logger.warning(
                    "winery_validation_failed",
                    code=data.code,
                    error="Code already exists"
                )
                raise DuplicateCodeError(
                    f"Winery code '{data.code}' already exists",
                    field="code",
                    value=data.code
                )
            
            # Delegate to repository (repository creates entity)
            winery = await self._winery_repo.create(data)
            
            logger.info(
                "winery_created_success",
                winery_id=winery.id,
                code=winery.code,
                name=winery.name
            )
            
            return winery
    
    # ==================================================================================
    # READ OPERATIONS
    # ==================================================================================
    
    async def get_winery(
        self,
        winery_id: int
    ) -> Winery:
        """Get winery by ID."""
        with LogTimer(logger, "get_winery_service"):
            logger.info(
                "getting_winery",
                winery_id=winery_id
            )
            
            winery = await self._winery_repo.get_by_id(winery_id)
            
            if not winery:
                logger.info(
                    "winery_not_found",
                    winery_id=winery_id
                )
                raise WineryNotFound(
                    f"Winery with ID {winery_id} not found",
                    winery_id=winery_id
                )
            
            logger.info(
                "winery_found",
                winery_id=winery_id,
                code=winery.code
            )
            
            return winery
    
    async def get_winery_by_code(
        self,
        code: str
    ) -> Winery:
        """Get winery by code."""
        with LogTimer(logger, "get_winery_by_code_service"):
            logger.info(
                "getting_winery_by_code",
                code=code
            )
            
            winery = await self._winery_repo.get_by_code(code)
            
            if not winery:
                logger.info(
                    "winery_not_found",
                    code=code
                )
                raise WineryNotFound(
                    f"Winery with code '{code}' not found",
                    code=code
                )
            
            logger.info(
                "winery_found",
                winery_id=winery.id,
                code=winery.code
            )
            
            return winery
    
    async def list_wineries(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Winery]:
        """List all wineries with pagination."""
        with LogTimer(logger, "list_wineries_service"):
            logger.info(
                "listing_wineries",
                skip=skip,
                limit=limit
            )
            
            wineries = await self._winery_repo.list_all(skip=skip, limit=limit)
            
            logger.info(
                "wineries_listed",
                count=len(wineries),
                skip=skip,
                limit=limit
            )
            
            return wineries
    
    # ==================================================================================
    # UPDATE OPERATIONS
    # ==================================================================================
    
    async def update_winery(
        self,
        winery_id: int,
        data: WineryUpdate
    ) -> Winery:
        """Update winery details."""
        with LogTimer(logger, "update_winery_service"):
            logger.info(
                "updating_winery",
                winery_id=winery_id
            )
            
            # Check winery exists
            winery = await self._winery_repo.get_by_id(winery_id)
            if not winery:
                logger.info(
                    "winery_not_found",
                    winery_id=winery_id
                )
                raise WineryNotFound(
                    f"Winery with ID {winery_id} not found",
                    winery_id=winery_id
                )
            
            # Validate name if provided
            if data.name is not None:
                if not data.name.strip():
                    logger.warning(
                        "winery_validation_failed",
                        winery_id=winery_id,
                        error="Name cannot be empty"
                    )
                    raise InvalidWineryData("Name cannot be empty", field="name")
            
            # Track changes for logging
            changes = {}
            if data.name and data.name != winery.name:
                changes["name"] = f"{winery.name} -> {data.name}"
            if data.location and data.location != winery.location:
                changes["location"] = f"{winery.location} -> {data.location}"
            if data.notes and data.notes != winery.notes:
                changes["notes"] = "updated"
            
            # Persist using repository update (id, data)
            updated_winery = await self._winery_repo.update(winery_id, data)
            
            logger.info(
                "winery_updated_success",
                winery_id=winery_id,
                code=winery.code,
                changes=changes
            )
            
            return updated_winery
    
    # ==================================================================================
    # DELETE OPERATIONS
    # ==================================================================================
    
    async def delete_winery(
        self,
        winery_id: int
    ) -> None:
        """Soft delete winery with active data protection."""
        with LogTimer(logger, "delete_winery_service"):
            logger.info(
                "deleting_winery",
                winery_id=winery_id
            )
            
            # Check winery exists
            winery = await self._winery_repo.get_by_id(winery_id)
            if not winery:
                logger.info(
                    "winery_not_found",
                    winery_id=winery_id
                )
                raise WineryNotFound(
                    f"Winery with ID {winery_id} not found",
                    winery_id=winery_id
                )
            
            # Check for active data in other modules (deletion protection)
            vineyards = await self._vineyard_repo.get_by_winery(winery_id)
            has_vineyards = len(vineyards) > 0
            
            fermentations = await self._fermentation_repo.get_by_winery(winery_id)
            has_fermentations = len(fermentations) > 0
            
            if has_vineyards or has_fermentations:
                details = []
                if has_vineyards:
                    details.append("vineyards")
                if has_fermentations:
                    details.append("fermentations")
                
                logger.warning(
                    "winery_deletion_blocked",
                    winery_id=winery_id,
                    code=winery.code,
                    active_vineyards=has_vineyards,
                    active_fermentations=has_fermentations
                )
                
                raise WineryHasActiveDataError(
                    f"Cannot delete winery '{winery.code}': has active data in modules: {', '.join(details)}",
                    winery_id=winery_id,
                    active_vineyards=has_vineyards,
                    active_fermentations=has_fermentations
                )
            
            # Safe to delete
            await self._winery_repo.delete(winery_id)
            
            logger.info(
                "winery_deleted_success",
                winery_id=winery_id,
                code=winery.code
            )
    
    # ==================================================================================
    # UTILITY OPERATIONS
    # ==================================================================================
    
    async def winery_exists(
        self,
        winery_id: int
    ) -> bool:
        """Check if winery exists."""
        with LogTimer(logger, "winery_exists_service"):
            winery = await self._winery_repo.get_by_id(winery_id)
            exists = winery is not None
            
            logger.info(
                "winery_exists_check",
                winery_id=winery_id,
                exists=exists
            )
            
            return exists
    
    async def count_wineries(self) -> int:
        """Count total wineries."""
        with LogTimer(logger, "count_wineries_service"):
            count = await self._winery_repo.count()
            
            logger.info(
                "wineries_counted",
                total=count
            )
            
            return count
