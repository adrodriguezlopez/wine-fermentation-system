"""
Fermentation API Request Schemas

Pydantic models for validating incoming requests to fermentation endpoints.
Implements field validation to ensure data integrity before service layer processing.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


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


class LotSourceRequest(BaseModel):
    """
    Request DTO for a single harvest lot source in a blend.
    
    Represents one harvest lot contributing to a fermentation.
    Used within FermentationWithBlendCreateRequest.
    """
    
    harvest_lot_id: int = Field(
        ...,
        gt=0,
        description="ID of the harvest lot to use"
    )
    
    mass_used_kg: Decimal = Field(
        ...,
        gt=0,
        description="Mass in kg taken from this lot (must be positive)",
        decimal_places=2
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional notes about this lot's contribution"
    )


class FermentationWithBlendCreateRequest(BaseModel):
    """
    Request DTO for creating a fermentation from multiple harvest lots (blend).
    
    Combines fermentation data with harvest lot sources for atomic creation.
    Uses UnitOfWork pattern to ensure all-or-nothing persistence.
    
    Example:
        ```json
        {
          "vintage_year": 2024,
          "yeast_strain": "EC-1118",
          "vessel_code": "TANK-01",
          "input_mass_kg": 100.0,
          "initial_sugar_brix": 22.5,
          "initial_density": 1.095,
          "start_date": "2024-11-22T10:00:00",
          "lot_sources": [
            {"harvest_lot_id": 1, "mass_used_kg": 60.0, "notes": "Block A"},
            {"harvest_lot_id": 2, "mass_used_kg": 40.0, "notes": "Block B"}
          ]
        }
        ```
    """
    
    # Fermentation base data
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
        description="Total input mass in kilograms (should equal sum of lot masses)"
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
    
    # Blend data
    lot_sources: List[LotSourceRequest] = Field(
        ...,
        min_length=1,
        description="List of harvest lots contributing to this fermentation (at least 1 required)"
    )
    
    @field_validator('lot_sources')
    @classmethod
    def validate_unique_lots(cls, v: List[LotSourceRequest]) -> List[LotSourceRequest]:
        """Ensure no duplicate harvest lot IDs."""
        lot_ids = [lot.harvest_lot_id for lot in v]
        if len(lot_ids) != len(set(lot_ids)):
            raise ValueError("Duplicate harvest_lot_id found. Each lot can only be used once.")
        return v
