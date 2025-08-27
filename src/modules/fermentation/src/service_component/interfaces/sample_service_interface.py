"""
Interface definition for the Sample Service.
Defines the contract that any sample service implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class ISampleService(ABC):
    """
    Interface for sample management service.
    Defines core operations for sample validation and retrieval.
    """

    @abstractmethod
    async def validate_sample(
        self, fermentation_id: int, timestamp: datetime, measurements: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validates a sample against business rules.

        Args:
            fermentation_id: ID of the fermentation this sample belongs to
            timestamp: When the sample was taken
            measurements: Dictionary with measurement values
            (glucose, ethanol, temperature)

        Returns:
            Dict[str, Any]: Validation results with any warnings or errors

        Raises:
            ValidationError: If measurements are invalid
            ChronologyError: If timestamp is not in correct sequence
        """
        pass

    @abstractmethod
    async def get_sample(self, fermentation_id: int, sample_id: int) -> Dict[str, Any]:
        """
        Retrieves a specific sample by ID.

        Args:
            fermentation_id: ID of the fermentation
            sample_id: ID of the sample to retrieve

        Returns:
            Dict[str, Any]: Sample data including measurements and metadata

        Raises:
            NotFoundError: If sample_id doesn't exist
            UnauthorizedError: If caller is not authorized to access this
            sample
        """
        pass

    @abstractmethod
    async def get_samples_in_range(
        self, fermentation_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all samples within a time range.

        Args:
            fermentation_id: ID of the fermentation
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            List[Dict[str, Any]]: List of samples in chronological order

        Raises:
            ValidationError: If time range is invalid
            UnauthorizedError: If caller is not authorized to access these
            samples
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
            UnauthorizedError: If caller is not authorized
            to access this fermentation
        """
        pass
