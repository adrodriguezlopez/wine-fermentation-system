"""
Interface definition for the Sample Service.

Service layer for sample management and validation.
Coordinates sample operations, validation, and business rules.

Follows Clean Architecture principles:
- Uses DTOs from domain layer (SampleCreate)
- Returns ORM entities (BaseSample) - no additional mapping needed
- Delegates data access to ISampleRepository
- Delegates validation to IValidationOrchestrator
- Does NOT handle authentication (API layer responsibility)

Following ADR-003 Separation of Concerns:
- SampleService handles ONLY sample operations
- Fermentation lifecycle operations are in IFermentationService (separate interface)
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.dtos import SampleCreate
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult


class ISampleService(ABC):
    """
    Interface for sample management service.
    
    Orchestrates:
    - Sample addition with full validation (chronology, values, business rules)
    - Sample queries with access control
    - Sample validation (dry-run)
    
    Does NOT handle:
    - Fermentation operations (use IFermentationService)
    - Authentication (API layer responsibility)
    - Direct database access (uses ISampleRepository)
    """

    # ==================================================================================
    # CREATION OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def add_sample(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int,
        data: SampleCreate
    ) -> BaseSample:
        """
        Adds a new sample with full validation.

        Business logic:
        1. Verifies fermentation exists and belongs to winery
        2. Verifies fermentation is not COMPLETED
        3. Validates sample completely:
           - Chronology validation (timestamp after last sample)
           - Value validation (range correct for sample_type)
           - Business rules (sugar decreasing, temperature in range)
        4. If validation OK: creates sample via repository
        5. Returns created sample

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            user_id: ID of user recording sample (audit)
            data: Sample creation data (DTO)

        Returns:
            BaseSample: Created sample entity with generated ID

        Raises:
            ValidationError: If sample is invalid
            NotFoundError: If fermentation doesn't exist
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # QUERY OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def get_sample(
        self,
        sample_id: int,
        fermentation_id: int,
        winery_id: int
    ) -> Optional[BaseSample]:
        """
        Retrieves a specific sample by ID.

        Business logic:
        1. Validates sample_id > 0
        2. Applies winery scoping (via fermentation)
        3. Returns sample or None

        Args:
            sample_id: ID of sample
            fermentation_id: ID of fermentation (access control)
            winery_id: Winery ID for access control

        Returns:
            Optional[BaseSample]: Sample entity or None if not found

        Raises:
            NotFoundError: If sample doesn't exist
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_samples_by_fermentation(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> List[BaseSample]:
        """
        Retrieves all samples for a fermentation in chronological order.

        Business logic:
        1. Verifies fermentation exists and belongs to winery
        2. Gets samples via repository
        3. Returns ordered by recorded_at ASC

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control

        Returns:
            List[BaseSample]: Samples in chronological order (can be empty list)

        Raises:
            NotFoundError: If fermentation doesn't exist
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_latest_sample(
        self,
        fermentation_id: int,
        winery_id: int,
        sample_type: Optional[SampleType] = None
    ) -> Optional[BaseSample]:
        """
        Retrieves the most recent sample (optionally filtered by type).

        Business logic:
        1. Verifies fermentation exists
        2. If sample_type provided: filters by type
        3. Returns most recent (recorded_at DESC LIMIT 1)

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            sample_type: Optional type filter (SUGAR, TEMPERATURE, DENSITY)

        Returns:
            Optional[BaseSample]: Latest sample or None if no samples exist

        Raises:
            NotFoundError: If fermentation doesn't exist
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_samples_in_timerange(
        self,
        fermentation_id: int,
        winery_id: int,
        start: datetime,
        end: datetime
    ) -> List[BaseSample]:
        """
        Retrieves samples within a specific time range.

        Business logic:
        1. Validates start < end
        2. Verifies fermentation exists and belongs to winery
        3. Gets samples in range via repository
        4. Returns ordered chronologically

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            start: Start of time range
            end: End of time range

        Returns:
            List[BaseSample]: Samples in range, chronologically ordered

        Raises:
            ValidationError: If time range is invalid (start >= end)
            NotFoundError: If fermentation doesn't exist
            RepositoryError: If database operation fails
        """
        pass

    # ==================================================================================
    # VALIDATION (Pre-creation checks)
    # ==================================================================================

    @abstractmethod
    async def validate_sample_data(
        self,
        fermentation_id: int,
        winery_id: int,
        data: SampleCreate
    ) -> ValidationResult:
        """
        Validates sample data before adding (dry-run).

        Useful for frontend validation before submitting form.

        Business logic:
        1. Verifies fermentation exists and belongs to winery
        2. Delegates to ValidationOrchestrator.validate_sample_complete()
        3. Does NOT create sample, only validates

        Args:
            fermentation_id: ID of fermentation
            winery_id: Winery ID for access control
            data: Sample data to validate

        Returns:
            ValidationResult: Validation result with errors/warnings

        Note: Does NOT add sample, only validates
        """
        pass

    # ==================================================================================
    # DELETION OPERATIONS
    # ==================================================================================

    @abstractmethod
    async def delete_sample(
        self,
        sample_id: int,
        fermentation_id: int,
        winery_id: int
    ) -> None:
        """
        Soft deletes a sample.

        Business logic:
        1. Verifies sample exists and belongs to fermentation
        2. Verifies fermentation belongs to winery (access control)
        3. Marks sample as deleted (soft delete)

        Args:
            sample_id: ID of sample to delete
            fermentation_id: ID of fermentation (access control)
            winery_id: Winery ID for access control

        Returns:
            None

        Raises:
            NotFoundError: If sample or fermentation doesn't exist
            RepositoryError: If database operation fails
        
        Status: ✅ Implemented via TDD (Phase 4 - 2025-10-22)
        """
        pass
