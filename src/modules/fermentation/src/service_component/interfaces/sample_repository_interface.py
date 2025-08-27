"""
Interface definition for the Sample Repository.
Defines the contract that any sample repository implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class ISampleRepository(ABC):
    """
    Interface for sample data persistence.
    Defines core operations for storing and retrieving fermentation samples.
    """

    @abstractmethod
    async def create_sample(
        self,
        fermentation_id: int,
        timestamp: datetime,
        measurements: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Creates a new sample record.

        Args:
            fermentation_id: ID of the fermentation this sample belongs to
            timestamp: When the sample was taken
            measurements: Dictionary with measurement values
            (glucose, ethanol, temperature)
            metadata: Optional metadata about the sample

        Returns:
            int: ID of the created sample

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If sample conflicts with existing data
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_sample_by_id(
        self, sample_id: int, fermentation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves a sample by its ID.

        Args:
            sample_id: ID of the sample to retrieve
            fermentation_id: Optional fermentation ID for access control

        Returns:
            Dict[str, Any]: Sample data including measurements and metadata

        Raises:
            NotFoundError: If sample_id doesn't exist
            UnauthorizedError: If fermentation_id doesn't match the sample
        """
        pass

    @abstractmethod
    async def get_samples_by_fermentation(
        self,
        fermentation_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves samples for a specific fermentation with pagination.

        Args:
            fermentation_id: ID of the fermentation
            limit: Maximum number of samples to return
            offset: Number of samples to skip

        Returns:
            List[Dict[str, Any]]: List of samples in chronological order

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_samples_in_timerange(
        self, fermentation_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieves samples within a specific time range.

        Args:
            fermentation_id: ID of the fermentation
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            List[Dict[str, Any]]: List of samples in chronological order

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If time range is invalid
        """
        pass

    @abstractmethod
    async def update_sample(
        self,
        sample_id: int,
        measurements: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Updates an existing sample's measurements or metadata.

        Args:
            sample_id: ID of the sample to update
            measurements: New measurement values (if updating measurements)
            metadata: New metadata (if updating metadata)

        Returns:
            bool: True if update was successful

        Raises:
            NotFoundError: If sample_id doesn't exist
            ValidationError: If measurements are invalid
            ConcurrencyError: If sample was modified by another process
        """
        pass

    @abstractmethod
    async def get_latest_sample(self, fermentation_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent sample for a fermentation.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            Optional[Dict[str, Any]]: Latest sample data or None if no samples
            exist

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass
