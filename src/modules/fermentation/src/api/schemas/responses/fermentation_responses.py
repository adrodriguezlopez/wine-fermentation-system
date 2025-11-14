"""
Response schemas for Fermentation endpoints

These Pydantic models define the structure of data returned by the API.
They convert domain entities to JSON-serializable DTOs.
"""

from datetime import datetime
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper
    
    Wraps a list of items with pagination metadata.
    Used for any list endpoint that supports pagination.
    """
    items: List[T] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items across all pages", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    size: int = Field(..., description="Number of items per page", ge=1, le=100)
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages"""
        if self.size == 0:
            return 0
        return (self.total + self.size - 1) // self.size


class FermentationResponse(BaseModel):
    """
    Response DTO for Fermentation entity
    
    Returns fermentation data to API clients with proper JSON serialization.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    # Primary key
    id: int = Field(..., description="Fermentation unique identifier")
    
    # Foreign keys
    winery_id: int = Field(..., description="Winery that owns this fermentation")
    
    # Wine production details
    vintage_year: int = Field(..., description="Harvest year", ge=1900, le=2100)
    yeast_strain: str = Field(..., description="Yeast strain used", max_length=100)
    vessel_code: Optional[str] = Field(None, description="Fermentation vessel code", max_length=50)
    
    # Initial measurements
    input_mass_kg: float = Field(..., description="Initial grape mass in kg", gt=0)
    initial_sugar_brix: float = Field(..., description="Initial sugar content in Brix", ge=0, le=50)
    initial_density: float = Field(..., description="Initial must density", gt=0)
    
    # Fermentation management
    status: str = Field(..., description="Current fermentation status", max_length=20)
    start_date: datetime = Field(..., description="Fermentation start date and time")
    
    # Audit fields
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @classmethod
    def from_entity(cls, fermentation: "Fermentation") -> "FermentationResponse":
        """
        Convert Fermentation entity to response DTO
        
        Args:
            fermentation: Domain entity from database
            
        Returns:
            FermentationResponse with data from entity
        """
        return cls(
            id=fermentation.id,
            winery_id=fermentation.winery_id,
            vintage_year=fermentation.vintage_year,
            yeast_strain=fermentation.yeast_strain,
            vessel_code=fermentation.vessel_code,
            input_mass_kg=fermentation.input_mass_kg,
            initial_sugar_brix=fermentation.initial_sugar_brix,
            initial_density=fermentation.initial_density,
            status=fermentation.status,
            start_date=fermentation.start_date,
            created_at=fermentation.created_at,
            updated_at=fermentation.updated_at,
        )
