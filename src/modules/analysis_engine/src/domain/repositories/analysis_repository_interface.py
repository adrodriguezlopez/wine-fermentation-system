"""
Repository interface for Analysis aggregate root.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ..entities.analysis import Analysis

from ..enums.analysis_status import AnalysisStatus


class IAnalysisRepository(ABC):
    """
    Repository interface for Analysis aggregate root.
    
    Handles persistence operations for Analysis entities including
    anomalies and recommendations (as part of the aggregate).
    """
    
    @abstractmethod
    async def add(self, analysis: 'Analysis') -> 'Analysis':
        """
        Add a new analysis to the repository.
        
        Args:
            analysis: The analysis model to persist
            
        Returns:
            The persisted analysis with any generated fields
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, analysis_id: UUID, winery_id: UUID) -> Optional['Analysis']:
        """
        Get an analysis by its ID.
        
        Args:
            analysis_id: The analysis ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            The analysis if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_fermentation_id(
        self, 
        fermentation_id: UUID, 
        winery_id: UUID
    ) -> List['Analysis']:
        """
        Get all analyses for a specific fermentation.
        
        Args:
            fermentation_id: The fermentation ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            List of analyses for the fermentation
        """
        pass
    
    @abstractmethod
    async def get_latest_by_fermentation_id(
        self, 
        fermentation_id: UUID, 
        winery_id: UUID
    ) -> Optional['Analysis']:
        """
        Get the most recent analysis for a fermentation.
        
        Args:
            fermentation_id: The fermentation ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            The latest analysis if exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_by_winery(
        self,
        winery_id: UUID,
        status: Optional[AnalysisStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List['Analysis']:
        """
        List analyses for a winery with optional filtering.
        
        Args:
            winery_id: The winery ID
            status: Optional status filter
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of analyses
        """
        pass
    
    @abstractmethod
    async def list_by_date_range(
        self,
        winery_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List['Analysis']:
        """
        List analyses within a date range for a winery.
        
        Args:
            winery_id: The winery ID
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of analyses
        """
        pass
    
    @abstractmethod
    async def update(self, analysis: 'Analysis') -> 'Analysis':
        """
        Update an existing analysis.
        
        Args:
            analysis: The analysis entity with updated data
            
        Returns:
            The updated analysis
        """
        pass
    
    @abstractmethod
    async def delete(self, analysis_id: UUID, winery_id: UUID) -> bool:
        """
        Delete an analysis by ID.
        
        Args:
            analysis_id: The analysis ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count_by_winery(
        self,
        winery_id: UUID,
        status: Optional[AnalysisStatus] = None
    ) -> int:
        """
        Count analyses for a winery.
        
        Args:
            winery_id: The winery ID
            status: Optional status filter
            
        Returns:
            Number of analyses
        """
        pass
