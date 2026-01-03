"""
Interface definition for the Sample Repository.
Defines the contract that any sample repository implementation must follow.
ARCHITECTURE: Repository returns BaseSample entities consistently across all methods.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


class ISampleRepository(ABC):
    """
    Interface for sample data persistence.
    Defines core operations for storing and retrieving fermentation samples.
    
    DESIGN PRINCIPLES:
    - Consistent return type: Always returns BaseSample entities
    - Upsert pattern: Single method for create/update operations
    - MVP-focused: No pagination, no metadata complexity
    - Repository pattern: Domain entities, not DTOs
    """

    @abstractmethod
    async def upsert_sample(self, sample: BaseSample) -> BaseSample:
        """
        Creates or updates a sample record using upsert pattern.
        
        UPSERT LOGIC:
        - If sample.id is None: INSERT new sample
        - If sample.id exists: UPDATE existing sample
        - Always returns the persisted BaseSample with ID populated

        Args:
            sample: BaseSample entity to create or update

        Returns:
            BaseSample: The persisted sample with ID and timestamps

        Raises:
            RepositoryError: If upsert operation fails
            IntegrityError: If sample conflicts with existing data
            NotFoundError: If updating non-existent sample
            ValidationError: If sample data is invalid
        """
        pass

    @abstractmethod
    async def get_sample_by_id(
        self, 
        sample_id: int, 
        fermentation_id: int,
        winery_id: int
    ) -> Optional[BaseSample]:
        """
        Retrieves a sample by its ID with winery access control (ADR-025).

        Args:
            sample_id: ID of the sample to retrieve
            fermentation_id: Fermentation ID for access control
            winery_id: Winery ID for multi-tenant security (REQUIRED)

        Returns:
            Optional[BaseSample]: Sample entity or None if not found or access denied

        Security:
            ADR-025 LIGHT: Validates that sample belongs to fermentation 
            AND fermentation belongs to winery. Returns None for cross-winery attempts.
        """
        pass

    @abstractmethod
    async def get_samples_by_fermentation_id(self, fermentation_id: int) -> List[BaseSample]:
        """
        Retrieves all samples for a specific fermentation as BaseSample entities.
        Used by ValidationService for chronological and trend validation.
        
        ORDERING: Returns samples in chronological order (recorded_at ASC)
        NO PAGINATION: Returns all samples for MVP simplicity

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            List[BaseSample]: List of sample entities in chronological order

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_samples_in_timerange(
        self, 
        fermentation_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[BaseSample]:
        """
        Retrieves samples within a specific time range as BaseSample entities.

        Args:
            fermentation_id: ID of the fermentation
            start_time: Start of the time range (inclusive)
            end_time: End of the time range (inclusive)

        Returns:
            List[BaseSample]: List of sample entities in chronological order

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If time range is invalid (start > end)
        """
        pass

    @abstractmethod
    async def get_latest_sample(self, fermentation_id: int) -> Optional[BaseSample]:
        """
        Retrieves the most recent sample for a fermentation as BaseSample entity.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            Optional[BaseSample]: Latest sample entity or None if no samples exist

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_fermentation_start_date(self, fermentation_id: int) -> datetime:
        """
        Retrieves the start date of a fermentation.
        Used by ValidationService to validate samples are not recorded before fermentation start.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            datetime: Start date of the fermentation in UTC

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_latest_sample_by_type(
        self, 
        fermentation_id: int, 
        sample_type: SampleType
    ) -> Optional[BaseSample]:
        """
        Retrieves the most recent sample of a specific type for a fermentation.
        Used by ValidationService for trend validation (e.g., sugar trend analysis).

        Args:
            fermentation_id: ID of the fermentation
            sample_type: Type of sample to retrieve (SUGAR, TEMPERATURE, DENSITY)

        Returns:
            Optional[BaseSample]: Latest sample of the specified type, or None if no samples exist

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass
    
    @abstractmethod
    async def check_duplicate_timestamp(
        self, 
        fermentation_id: int, 
        sample: BaseSample, 
        exclude_sample_id: Optional[int] = None
    ) -> bool:
        """
        Checks if a sample with the same recorded_at timestamp and the same sample_type already exists for the fermentation.
        Used by ValidationService to enforce unique timestamps per fermentation.

        Args:
            fermentation_id: ID of the fermentation
            sample: The sample to check for duplicates
            exclude_sample_id: Optional sample ID to exclude from the check (useful during updates)

        Returns:
            bool: True if a duplicate timestamp exists, False otherwise

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If recorded_at is invalid
        """
        pass


    @abstractmethod
    async def soft_delete_sample(self, sample_id: int) -> None:
        """
        Soft deletes a sample by marking it as deleted without removing it from the database.
        Used to maintain historical data integrity while allowing logical deletion.

        Args:
            sample_id: ID of the sample to soft delete

        Returns:
            None

        Raises:
            NotFoundError: If sample_id doesn't exist
            RepositoryError: If soft delete operation fails
        """
        pass

    @abstractmethod
    async def bulk_upsert_samples(self, samples: List[BaseSample]) -> List[BaseSample]:
        """
        Performs bulk upsert (create or update) of multiple samples.
        Used for batch operations to improve performance.

        UPSERT LOGIC:
        - If sample.id is None: INSERT new sample
        - If sample.id exists: UPDATE existing sample
        - Always returns the list of persisted BaseSample entities with IDs populated

        Args:
            samples: List[BaseSample] entities to create or update
        Returns:
            List[BaseSample]: List of persisted samples with IDs and timestamps
        Raises:
            RepositoryError: If bulk upsert operation fails
            IntegrityError: If any sample conflicts with existing data
            NotFoundError: If updating non-existent samples
            ValidationError: If any sample data is invalid
        """
        pass

    @abstractmethod
    async def list_by_data_source(
        self, fermentation_id: int, data_source: str, winery_id: int
    ) -> List[BaseSample]:
        """
        Retrieves samples filtered by data source (ADR-029).

        Args:
            fermentation_id: ID of the fermentation
            data_source: Data source to filter by ('system', 'imported', 'migrated')
            winery_id: Winery ID for multi-tenant security (REQUIRED)

        Returns:
            List[BaseSample]: List of samples with specified data source

        Raises:
            RepositoryError: If database operation fails
            NotFoundError: If fermentation doesn't exist or access denied
        """
        pass
