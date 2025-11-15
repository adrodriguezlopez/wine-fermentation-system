"""
Fermentation API Request Schemas

Pydantic models for validating incoming requests to fermentation endpoints.
Implements field validation to ensure data integrity before service layer processing.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FermentationCreateRequest(BaseModel):
    """
    Request DTO for creating a new fermentation
    
    All fields are required except vessel_code.
    Validates data types, ranges, and string lengths.
    """
    
    vintage_year: int = Field(
        ..., 
        ge=1900, 
        le=2100,
        description="Harvest year (1900-2100)"
    )
    
    yeast_strain: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="Yeast strain identifier"
    )
    
    vessel_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional vessel/tank identifier"
    )
    
    input_mass_kg: float = Field(
        ...,
        gt=0,
        description="Initial grape mass in kilograms (must be positive)"
    )
    
    initial_sugar_brix: float = Field(
        ...,
        ge=0,
        le=50,
        description="Initial sugar content in °Brix (0-50)"
    )
    
    initial_density: float = Field(
        ...,
        gt=0,
        description="Initial must density (must be positive)"
    )
    
    start_date: datetime = Field(
        ...,
        description="Fermentation start date and time"
    )


class FermentationUpdateRequest(BaseModel):
    """
    Request DTO for updating an existing fermentation
    
    All fields are optional to support partial updates.
    Only provided fields will be updated in the service layer.
    """
    
    status: Optional[str] = Field(
        None,
        max_length=20,
        description="Fermentation status"
    )
    
    yeast_strain: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Yeast strain identifier"
    )
    
    vessel_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Vessel/tank identifier"
    )
    
    input_mass_kg: Optional[float] = Field(
        None,
        gt=0,
        description="Initial grape mass in kilograms"
    )
    
    initial_sugar_brix: Optional[float] = Field(
        None,
        ge=0,
        le=50,
        description="Initial sugar content in °Brix"
    )
    
    initial_density: Optional[float] = Field(
        None,
        gt=0,
        description="Initial must density"
    )
    
    vintage_year: Optional[int] = Field(
        None,
        ge=1900,
        le=2100,
        description="Harvest year"
    )
    
    start_date: Optional[datetime] = Field(
        None,
        description="Fermentation start date and time"
    )


class StatusUpdateRequest(BaseModel):
    """
    Request DTO for updating fermentation status
    
    Used for PATCH /fermentations/{id}/status endpoint.
    Validates status transitions via service layer.
    """
    
    status: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="New fermentation status (e.g., IN_PROGRESS, COMPLETED, PAUSED)"
    )


class CompleteFermentationRequest(BaseModel):
    """
    Request DTO for completing a fermentation
    
    Used for PATCH /fermentations/{id}/complete endpoint.
    Requires final metrics to calculate yields and outcomes.
    """
    
    final_sugar_brix: float = Field(
        ...,
        ge=0,
        le=50,
        description="Final residual sugar in °Brix (0-50)"
    )
    
    final_mass_kg: float = Field(
        ...,
        gt=0,
        description="Final mass after fermentation in kilograms (must be positive)"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional completion notes or observations"
    )
