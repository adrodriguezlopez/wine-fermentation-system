"""
Interface definition for the Fermentation Service.
Defines the contract that any fermentation service implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class IFermentationService(ABC):
    """
    Interface for fermentation management service.
    Defines core operations for fermentation lifecycle and sample management.
    """
    
    @abstractmethod
    async def create_fermentation(self, winery_id: int, initial_data: Dict[str, Any]) -> int:
        """
        Creates a new fermentation process.

        Args:
            winery_id: Identifier of the winery starting the fermentation
            initial_data: Initial parameters and metadata for the fermentation

        Returns:
            int: The ID of the created fermentation

        Raises:
            ValidationError: If initial data is invalid
            UnauthorizedError: If winery_id is not authorized
        """
        pass

    @abstractmethod
    async def get_fermentation(self, fermentation_id: int) -> Dict[str, Any]:
        """
        Retrieves fermentation data by ID.

        Args:
            fermentation_id: The ID of the fermentation to retrieve

        Returns:
            Dict[str, Any]: Fermentation data including status and metadata

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            UnauthorizedError: If caller is not authorized to access this fermentation
        """
        pass

    @abstractmethod
    async def add_sample(
        self, 
        fermentation_id: int, 
        timestamp: datetime,
        measurements: Dict[str, float]
    ) -> bool:
        """
        Adds a new sample measurement to a fermentation.

        Args:
            fermentation_id: The ID of the fermentation
            timestamp: When the sample was taken
            measurements: Dictionary with measurement values (glucose, ethanol, temperature)

        Returns:
            bool: True if sample was added successfully

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If measurements are invalid or out of expected ranges
            ChronologyError: If timestamp is not in correct sequence
            UnauthorizedError: If caller is not authorized to add samples
        """
        pass
