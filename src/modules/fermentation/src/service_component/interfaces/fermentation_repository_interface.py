"""
Interface definition for the Fermentation Repository.
Defines the contract that any repository implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class IFermentationRepository(ABC):
    """
    Interface for fermentation data persistence.
    Defines core operations for storing and retrieving fermentation data.
    """

    @abstractmethod
    async def create(
            self,
            winery_id: int,
            initial_data: Dict[str, Any]
            ) -> int:
        """
        Creates a new fermentation record.

        Args:
            winery_id: ID of the winery starting the fermentation
            initial_data: Initial fermentation parameters and metadata

        Returns:
            int: ID of the created fermentation

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated
        """
        pass

    @abstractmethod
    async def get_by_id(
        self, fermentation_id: int, winery_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves a fermentation by its ID.

        Args:
            fermentation_id: ID of the fermentation to retrieve
            winery_id: Optional winery ID for access control

        Returns:
            Dict[str, Any]: Fermentation data including status and metadata

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            UnauthorizedError: If winery_id doesn't match the fermentation
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        fermentation_id: int,
        new_status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Updates the status of a fermentation.

        Args:
            fermentation_id: ID of the fermentation
            new_status: New status value
            metadata: Optional metadata about the status change

        Returns:
            bool: True if update was successful

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If new_status is invalid
        """
        pass

    @abstractmethod
    async def add_sample(
        self,
        fermentation_id: int,
        timestamp: datetime,
        measurements: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Adds a new sample to a fermentation.

        Args:
            fermentation_id: ID of the fermentation
            timestamp: When the sample was taken
            measurements: Sample measurement values
            metadata: Optional sample metadata

        Returns:
            int: ID of the created sample

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If measurements are invalid
            IntegrityError: If sample conflicts with existing data
        """
        pass

    @abstractmethod
    async def get_samples(
        self,
        fermentation_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves samples for a fermentation with pagination.

        Args:
            fermentation_id: ID of the fermentation
            limit: Maximum number of samples to return
            offset: Number of samples to skip

        Returns:
            List[Dict[str, Any]]: List of sample records

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_samples_in_range(
        self, fermentation_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieves samples within a time range.

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
    async def get_latest_sample(
            self,
            fermentation_id: int
            ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent sample for a fermentation.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            Optional[Dict[str, Any]]: Latest sample or None if no samples exist

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def get_by_status(
        self, status: str, winery_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves fermentations by their current status.

        Args:
            status: Status to filter by
            winery_id: Optional winery ID for filtering

        Returns:
            List[Dict[str, Any]]: List of fermentations with the specified
            status

        Raises:
            ValidationError: If status is invalid
        """
        pass

    @abstractmethod
    async def get_by_winery(
        self, winery_id: int, include_completed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all fermentations for a winery.

        Args:
            winery_id: ID of the winery
            include_completed: Whether to include completed fermentations

        Returns:
            List[Dict[str, Any]]: List of fermentations for the winery

        Raises:
            NotFoundError: If winery_id doesn't exist
        """
        pass
