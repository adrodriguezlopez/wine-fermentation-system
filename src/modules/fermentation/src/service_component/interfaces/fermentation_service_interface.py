"""
Interface definition for the Fermentation Service.

Service layer for fermentation business logic orchestration.
Coordinates validation, repository access, and business rules.

Follows Clean Architecture principles:
- Uses DTOs from domain layer (FermentationCreate)
- Returns ORM entities (Fermentation) - no additional mapping needed
- Delegates data access to IFermentationRepository
- Delegates validation to IValidationOrchestrator
- Does NOT handle authentication (API layer responsibility)
- Does NOT handle sample operations (ISampleService responsibility - ADR-003)

Following ADR-003 Separation of Concerns:
- FermentationService handles ONLY fermentation lifecycle operations
- Sample operations are in ISampleService (separate interface)
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos import FermentationCreate, FermentationUpdate, FermentationWithBlendCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork


class IFermentationService(ABC):
    """
    Interface for fermentation lifecycle management.
    
    Orchestrates:
    - Fermentation creation with validation
    - Status transitions with business rules
    - Fermentation queries with access control
    - Business logic coordination
    
    Does NOT handle:
    - Sample operations (use ISampleService)
    - Authentication (API layer responsibility)
    - Direct database access (uses IFermentationRepository)
    """

    # ==================================================================================
    # CREATION OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def create_fermentation(
        self,
        winery_id: int,
        user_id: int,
        data: FermentationCreate
    ) -> Fermentation:
        """
        Creates a new fermentation with full validation.

        Business logic:
        1. Validates fermentation data (initial values, ranges)
        2. Checks business rules (vintage year, vessel availability)
        3. Creates fermentation record
        4. Applies default status (ACTIVE)
        5. Records audit trail (created_by, created_at)

        Args:
            winery_id: ID of the winery (multi-tenant scoping)
            user_id: ID of user creating fermentation (audit trail)
            data: Fermentation creation data (DTO)

        Returns:
            Fermentation: Created fermentation entity with generated ID

        Raises:
            ValidationError: If data is invalid (e.g., negative values, invalid year)
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def create_fermentation_with_blend(
        self,
        winery_id: int,
        user_id: int,
        data: FermentationWithBlendCreate,
        uow: IUnitOfWork
    ) -> Fermentation:
        """
        Creates a fermentation from multiple harvest lots (blend) atomically.
        
        Uses UnitOfWork pattern to ensure fermentation and all lot sources
        are created together or not at all. Critical for data integrity in blends.
        
        Business logic:
        1. Validates fermentation base data
        2. Validates all harvest lots exist and belong to winery
        3. Validates mass consistency (sum of lots == fermentation mass)
        4. Validates lot availability (not exhausted)
        5. Creates fermentation record
        6. Creates all lot source records
        7. Commits transaction atomically
        
        Use Case (ADR-001 Fruit Origin Model):
        - Creating wine blends from multiple vineyard blocks
        - Tracking grape origin for regulatory/quality purposes
        - Maintaining referential integrity across fermentation + lot sources
        
        Args:
            winery_id: ID of the winery (multi-tenant scoping)
            user_id: ID of user creating fermentation (audit trail)
            data: Fermentation + blend data (DTO)
            uow: Unit of Work for atomic transaction
        
        Returns:
            Fermentation: Created fermentation entity with generated ID
        
        Raises:
            ValidationError: If blend data is invalid
                - Lot doesn't exist or doesn't belong to winery
                - Mass mismatch (sum != fermentation mass)
                - Lot already exhausted
                - Duplicate lot IDs
            RepositoryError: If database operation fails
        
        Example:
            ```python
            data = FermentationWithBlendCreate(
                fermentation_data=FermentationCreate(...),
                lot_sources=[
                    LotSourceData(harvest_lot_id=1, mass_used_kg=60.0),
                    LotSourceData(harvest_lot_id=2, mass_used_kg=40.0)
                ]
            )
            
            async with uow:
                fermentation = await service.create_fermentation_with_blend(
                    winery_id=1, user_id=1, data=data, uow=uow
                )
                # Auto-rollback on exception, explicit commit in service
            ```
        
        Status: ⏳ NEW - Part of UnitOfWork implementation (Nov 22, 2025)
        """
        pass

    # ==================================================================================
    # QUERY OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def get_fermentation(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> Optional[Fermentation]:
        """
        Retrieves a fermentation by ID with access control.

        Business logic:
        1. Validates access (winery_id scoping)
        2. Retrieves fermentation
        3. Filters soft-deleted records

        Args:
            fermentation_id: ID of fermentation to retrieve
            winery_id: Winery ID for access control

        Returns:
            Optional[Fermentation]: Fermentation entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_fermentations_by_winery(
        self,
        winery_id: int,
        status: Optional[FermentationStatus] = None,
        include_completed: bool = False,
        data_source: Optional[str] = None
    ) -> List[Fermentation]:
        """
        Retrieves fermentations for a winery with optional filters.

        Business logic:
        1. Applies winery scoping
        2. Filters by status if provided
        3. Optionally includes/excludes completed fermentations
        4. Filters by data source if provided (ADR-034)
        5. Returns list ordered by start_date DESC

        Args:
            winery_id: ID of the winery
            status: Optional status filter
            include_completed: Whether to include completed fermentations
            data_source: Optional data source filter (SYSTEM, HISTORICAL, MIGRATED) - ADR-034

        Returns:
            List[Fermentation]: List of fermentations matching criteria

        Raises:
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # UPDATE OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def update_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int,
        data: FermentationUpdate
    ) -> Fermentation:
        """
        Updates an existing fermentation with partial data.

        Business logic:
        1. Validates access (winery scoping)
        2. Validates update data
        3. Applies partial updates (only provided fields)
        4. Updates modification audit trail
        5. Returns updated entity

        Args:
            fermentation_id: ID of fermentation to update
            winery_id: Winery ID for access control
            user_id: ID of user making update (audit)
            data: Partial update data (only provided fields updated)

        Returns:
            Fermentation: Updated fermentation entity

        Raises:
            NotFoundError: If fermentation not found
            ValidationError: If update data is invalid
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # STATUS MANAGEMENT
    # ==================================================================================

    @abstractmethod
    async def update_status(
        self,
        fermentation_id: int,
        winery_id: int,
        new_status: FermentationStatus,
        user_id: int
    ) -> Fermentation:
        """
        Updates fermentation status with business rule validation.

        Business logic:
        1. Validates status transition (ACTIVE → SLOW → STUCK → COMPLETED)
        2. Checks prerequisites (e.g., minimum samples for COMPLETED)
        3. Updates status
        4. Records audit trail (who, when)

        Valid transitions:
        - ACTIVE → SLOW (fermentation slowing down)
        - SLOW → STUCK (fermentation stalled)
        - SLOW → ACTIVE (resumed)
        - ACTIVE → COMPLETED (finished normally)
        - STUCK → COMPLETED (ended prematurely)

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            new_status: Target status
            user_id: ID of user making the change (audit)

        Returns:
            Fermentation: Updated fermentation entity

        Raises:
            NotFoundError: If fermentation not found
            ValidationError: If status transition is invalid
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def complete_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int,
        completion_notes: Optional[str] = None
    ) -> Fermentation:
        """
        Marks a fermentation as completed with validation.

        Business logic:
        1. Validates fermentation can be completed (minimum samples, status)
        2. Calculates final metrics (duration, yields)
        3. Updates status to COMPLETED
        4. Sets end_date
        5. Archives related data

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            user_id: ID of user completing (audit)
            completion_notes: Optional notes about completion

        Returns:
            Fermentation: Completed fermentation entity

        Raises:
            NotFoundError: If fermentation not found
            ValidationError: If fermentation cannot be completed
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # SOFT DELETE
    # ==================================================================================

    @abstractmethod
    async def soft_delete(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft deletes a fermentation (sets is_deleted=True).

        Business logic:
        1. Validates fermentation exists and belongs to winery
        2. Checks if fermentation can be deleted
        3. Marks as deleted (is_deleted=True)
        4. Records deletion audit trail

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            user_id: ID of user deleting (audit)

        Returns:
            bool: True if deleted successfully

        Raises:
            NotFoundError: If fermentation not found
            ValidationError: If deletion not allowed
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # VALIDATION (Pre-creation checks)
    # ==================================================================================

    @abstractmethod
    async def validate_creation_data(
        self,
        data: FermentationCreate
    ) -> ValidationResult:
        """
        Validates fermentation data before creation (dry-run).

        Useful for frontend validation before submitting form.

        Business logic:
        1. Validates data types and ranges
        2. Checks business rules
        3. Returns detailed validation results

        Args:
            data: Fermentation data to validate

        Returns:
            ValidationResult: Validation result with errors/warnings

        Note: Does NOT create fermentation, only validates
        """
        pass
