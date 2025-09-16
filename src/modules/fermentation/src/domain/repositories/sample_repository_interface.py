"""
Interface definition for the Sample Repository.
Defines the contract that any sample repository implementation must follow.
ARCHITECTURE: Repository returns BaseSample entities consistently across all methods.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from domain.entities.samples.base_sample import BaseSample
from domain.enums.sample_type import SampleType


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
        fermentation_id: Optional[int] = None
    ) -> BaseSample:
        """
        Retrieves a sample by its ID as BaseSample entity.

        Args:
            sample_id: ID of the sample to retrieve
            fermentation_id: Optional fermentation ID for access control

        Returns:
            BaseSample: Sample entity with all properties

        Raises:
            NotFoundError: If sample_id doesn't exist
            UnauthorizedError: If fermentation_id doesn't match the sample
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
    async def get_fermentation_temperature_range(self, fermentation_id: int) -> Tuple[float, float]:
        """
        Retrieves the acceptable temperature range for a specific fermentation.
        Used by ValidationService to validate temperature samples.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            (float, float): Tuple of (min_temperature, max_temperature)

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass