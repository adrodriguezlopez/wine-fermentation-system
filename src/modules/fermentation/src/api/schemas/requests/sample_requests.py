"""
Sample API Request Schemas

Pydantic models for validating incoming requests to sample endpoints.
Implements field validation for sample measurement data.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SampleCreateRequest(BaseModel):
    """
    Request DTO for creating a new sample measurement
    
    All fields are required.
    Validates data types, string lengths, and value ranges.
    """
    
    sample_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of sample measurement (e.g., 'glucose', 'temperature')"
    )
    
    value: float = Field(
        ...,
        description="Measured value"
    )
    
    units: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Units of measurement (e.g., 'g/L', '°C')"
    )
    
    recorded_at: datetime = Field(
        ...,
        description="Timestamp when sample was recorded"
    )


class SampleUpdateRequest(BaseModel):
    """
    Request DTO for updating an existing sample
    
    All fields are optional to support partial updates.
    Only provided fields will be updated in the service layer.
    """
    
    sample_type: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Type of sample measurement"
    )
    
    value: Optional[float] = Field(
        None,
        description="Measured value"
    )
    
    units: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Units of measurement"
    )
    
    recorded_at: Optional[datetime] = Field(
        None,
        description="Timestamp when sample was recorded"
    )
