"""
Repository interface for RecommendationTemplate entity.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.recommendation_template import RecommendationTemplate
from ..enums.anomaly_type import AnomalyType
from ..enums.recommendation_category import RecommendationCategory


class IRecommendationTemplateRepository(ABC):
    """
    Repository interface for RecommendationTemplate entity.
    
    Templates are used to generate consistent recommendations
    across analyses.
    """
    
    @abstractmethod
    async def add(self, template: RecommendationTemplate) -> RecommendationTemplate:
        """
        Add a new recommendation template.
        
        Args:
            template: The template to persist
            
        Returns:
            The persisted template
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, template_id: UUID) -> Optional[RecommendationTemplate]:
        """
        Get a template by its ID.
        
        Args:
            template_id: The template ID
            
        Returns:
            The template if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[RecommendationTemplate]:
        """
        Get a template by its unique code.
        
        Args:
            code: The template code (e.g., "TEMP_ADJUST_HIGH")
            
        Returns:
            The template if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_by_category(
        self,
        category: RecommendationCategory,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """
        List templates by category.
        
        Args:
            category: The recommendation category
            is_active: Filter for active templates only
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of templates
        """
        pass
    
    @abstractmethod
    async def list_by_anomaly_type(
        self,
        anomaly_type: AnomalyType,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """
        List templates applicable to a specific anomaly type.
        
        Args:
            anomaly_type: The anomaly type
            is_active: Filter for active templates only
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of applicable templates
        """
        pass
    
    @abstractmethod
    async def list_active(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """
        List all active templates.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active templates
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """
        List all templates (active and inactive).
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of all templates
        """
        pass
    
    @abstractmethod
    async def update(self, template: RecommendationTemplate) -> RecommendationTemplate:
        """
        Update an existing template.
        
        Args:
            template: The template with updated data
            
        Returns:
            The updated template
        """
        pass
    
    @abstractmethod
    async def delete(self, template_id: UUID) -> bool:
        """
        Delete a template by ID.
        
        Args:
            template_id: The template ID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count_active(self) -> int:
        """
        Count active templates.
        
        Returns:
            Number of active templates
        """
        pass
    
    @abstractmethod
    async def get_most_used(
        self,
        limit: int = 10
    ) -> List[RecommendationTemplate]:
        """
        Get the most frequently used templates.
        
        Args:
            limit: Maximum number of templates to return
            
        Returns:
            List of templates ordered by times_applied (descending)
        """
        pass
