"""
Repository interface for Recommendation entity.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.recommendation import Recommendation


class IRecommendationRepository(ABC):
    """
    Repository interface for Recommendation entity.
    
    Note: Recommendations are typically managed through the Analysis aggregate,
    but this repository provides direct access for queries and tracking.
    """
    
    @abstractmethod
    async def get_by_id(self, recommendation_id: UUID) -> Optional[Recommendation]:
        """
        Get a recommendation by its ID.
        
        Args:
            recommendation_id: The recommendation ID
            
        Returns:
            The recommendation if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_analysis_id(self, analysis_id: UUID) -> List[Recommendation]:
        """
        Get all recommendations for a specific analysis.
        
        Args:
            analysis_id: The analysis ID
            
        Returns:
            List of recommendations for the analysis
        """
        pass
    
    @abstractmethod
    async def get_by_anomaly_id(self, anomaly_id: UUID) -> List[Recommendation]:
        """
        Get all recommendations addressing a specific anomaly.
        
        Args:
            anomaly_id: The anomaly ID
            
        Returns:
            List of recommendations for the anomaly
        """
        pass
    
    @abstractmethod
    async def get_by_fermentation_id(
        self, 
        fermentation_id: UUID,
        winery_id: UUID
    ) -> List[Recommendation]:
        """
        Get all recommendations for a specific fermentation.
        
        Args:
            fermentation_id: The fermentation ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            List of recommendations for the fermentation
        """
        pass
    
    @abstractmethod
    async def list_by_template(
        self,
        winery_id: UUID,
        template_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """
        List recommendations by template for a winery.
        
        Args:
            winery_id: The winery ID
            template_id: The recommendation template ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations
        """
        pass
    
    @abstractmethod
    async def list_by_priority(
        self,
        winery_id: UUID,
        min_priority: int = 1,
        max_priority: Optional[int] = None,
        is_applied: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """
        List recommendations by priority range for a winery.
        
        Args:
            winery_id: The winery ID
            min_priority: Minimum priority (1=highest)
            max_priority: Optional maximum priority
            is_applied: Optional filter for applied status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations ordered by priority
        """
        pass
    
    @abstractmethod
    async def list_unapplied(
        self,
        winery_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """
        List unapplied recommendations for a winery.
        
        Args:
            winery_id: The winery ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of unapplied recommendations ordered by priority
        """
        pass
    
    @abstractmethod
    async def count_by_template(
        self,
        winery_id: UUID,
        template_id: UUID,
        is_applied: Optional[bool] = None
    ) -> int:
        """
        Count recommendations by template for a winery.
        
        Args:
            winery_id: The winery ID
            template_id: The recommendation template ID
            is_applied: Optional filter for applied status
            
        Returns:
            Number of recommendations
        """
        pass
    
    @abstractmethod
    async def get_application_rate_by_template(
        self,
        winery_id: UUID,
        template_id: UUID
    ) -> float:
        """
        Calculate the application rate for a template.
        
        Args:
            winery_id: The winery ID
            template_id: The recommendation template ID
            
        Returns:
            Application rate (0.0 to 1.0)
        """
        pass
