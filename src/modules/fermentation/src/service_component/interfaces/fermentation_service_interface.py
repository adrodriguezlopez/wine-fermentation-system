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
from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult


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
        include_completed: bool = False
    ) -> List[Fermentation]:
        """
        Retrieves fermentations for a winery with optional filters.

        Business logic:
        1. Applies winery scoping
        2. Filters by status if provided
        3. Optionally includes/excludes completed fermentations
        4. Returns list ordered by start_date DESC

        Args:
            winery_id: ID of the winery
            status: Optional status filter
            include_completed: Whether to include completed fermentations

        Returns:
            List[Fermentation]: List of fermentations matching criteria

        Raises:
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
