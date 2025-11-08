"""
Response schemas for Sample endpoints

These Pydantic models define the structure of sample data returned by the API.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SampleResponse(BaseModel):
    """
    Response DTO for Sample (BaseSample) entity
    
    Returns sample measurement data to API clients.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    # Primary key
    id: int = Field(..., description="Sample unique identifier")
    
    # Sample context
    fermentation_id: int = Field(..., description="Associated fermentation ID")
    sample_type: str = Field(..., description="Type of sample (glucose, ethanol, temperature, etc.)", max_length=50)
    
    # Measurement data
    value: float = Field(..., description="Measured value")
    units: str = Field(..., description="Measurement units (g/L, °C, etc.)", max_length=20)
    
    # Timing
    recorded_at: datetime = Field(..., description="When the sample was taken")
    
    # Audit fields
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @classmethod
    def from_entity(cls, sample: "BaseSample") -> "SampleResponse":
        """
        Convert BaseSample entity to response DTO
        
        Args:
            sample: Domain entity from database
            
        Returns:
            SampleResponse with data from entity
        """
        return cls(
            id=sample.id,
            fermentation_id=sample.fermentation_id,
            sample_type=sample.sample_type,
            value=sample.value,
            units=sample.units,
            recorded_at=sample.recorded_at,
            created_at=sample.created_at,
            updated_at=sample.updated_at,
        )
