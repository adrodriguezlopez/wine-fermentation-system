"""
Harvest Lot Request DTOs for API Layer.

Pydantic v2 models for validating harvest lot API requests.
Converts API input to domain DTOs for service layer.

Related ADRs:
- ADR-015: Fruit Origin API Design
- ADR-001: Fruit Origin Model
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date, time
from typing import Optional


class HarvestLotCreateRequest(BaseModel):
    """
    Request DTO for creating a harvest lot.
    
    Required fields: block_id, code, harvest_date, weight_kg
    Optional fields: All Brix, variety, and harvest detail fields
    
    Validations:
    - code: Alphanumeric with hyphens/underscores, auto-uppercased
    - harvest_date: Must be a valid date (≤ today validated by service)
    - weight_kg: Must be positive
    - brix_at_harvest: 0-40 range if provided
    - pick_start_time/pick_end_time: Valid time strings (HH:MM or HH:MM:SS)
    """
    block_id: int = Field(..., gt=0, description="ID of vineyard block (must belong to user's winery)")
    code: str = Field(..., min_length=1, max_length=50, description="Unique harvest lot code")
    harvest_date: date = Field(..., description="Date fruit was harvested")
    weight_kg: float = Field(..., gt=0, description="Total weight in kilograms (must be positive)")
    
    # Brix measurements (optional)
    brix_at_harvest: Optional[float] = Field(None, ge=0, le=40, description="Sugar content in Brix (0-40)")
    brix_method: Optional[str] = Field(None, max_length=50, description="Measurement method (e.g., 'refractometer', 'hydrometer')")
    brix_measured_at: Optional[str] = Field(None, max_length=50, description="Measurement location (e.g., 'field', 'receival')")
    
    # Grape details (optional)
    grape_variety: Optional[str] = Field(None, max_length=100, description="Grape variety (e.g., 'Chardonnay', 'Pinot Noir')")
    clone: Optional[str] = Field(None, max_length=50, description="Clone identifier (e.g., 'Clone 95', 'Dijon 115')")
    rootstock: Optional[str] = Field(None, max_length=50, description="Rootstock type (e.g., '101-14', '3309C')")
    
    # Harvest details (optional)
    pick_method: Optional[str] = Field(None, max_length=20, description="Picking method ('hand' or 'machine')")
    pick_start_time: Optional[str] = Field(None, max_length=8, description="Pick start time (HH:MM or HH:MM:SS)")
    pick_end_time: Optional[str] = Field(None, max_length=8, description="Pick end time (HH:MM or HH:MM:SS)")
    bins_count: Optional[int] = Field(None, ge=0, description="Number of bins/containers")
    field_temp_c: Optional[float] = Field(None, ge=-50, le=60, description="Field temperature in Celsius")
    notes: Optional[str] = Field(None, max_length=255, description="Optional notes")
    
    @field_validator('code')
    @classmethod
    def code_must_be_valid(cls, v: str) -> str:
        """Validate code format and auto-uppercase."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()
    
    @field_validator('pick_method')
    @classmethod
    def pick_method_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate pick method is hand or machine."""
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ['hand', 'machine']:
                raise ValueError("Pick method must be 'hand' or 'machine'")
            return v_lower
        return v
    
    @field_validator('pick_start_time', 'pick_end_time')
    @classmethod
    def time_must_be_valid_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format HH:MM or HH:MM:SS."""
        if v is not None:
            # Try to parse as time to validate format
            try:
                # Support both HH:MM and HH:MM:SS formats
                if len(v) == 5:  # HH:MM
                    time.fromisoformat(v + ':00')
                elif len(v) == 8:  # HH:MM:SS
                    time.fromisoformat(v)
                else:
                    raise ValueError('Time must be in HH:MM or HH:MM:SS format')
            except ValueError as e:
                raise ValueError(f'Invalid time format: {e}')
        return v


class HarvestLotUpdateRequest(BaseModel):
    """
    Request DTO for updating a harvest lot.
    
    All fields are optional to support partial updates.
    Only provided (non-None) fields will be updated.
    
    Note: Cannot change block_id after creation (business rule).
    """
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Updated harvest lot code")
    harvest_date: Optional[date] = Field(None, description="Updated harvest date")
    weight_kg: Optional[float] = Field(None, gt=0, description="Updated weight in kilograms")
    
    # Brix measurements
    brix_at_harvest: Optional[float] = Field(None, ge=0, le=40, description="Updated Brix measurement")
    brix_method: Optional[str] = Field(None, max_length=50, description="Updated measurement method")
    brix_measured_at: Optional[str] = Field(None, max_length=50, description="Updated measurement location")
    
    # Grape details
    grape_variety: Optional[str] = Field(None, max_length=100, description="Updated grape variety")
    clone: Optional[str] = Field(None, max_length=50, description="Updated clone")
    rootstock: Optional[str] = Field(None, max_length=50, description="Updated rootstock")
    
    # Harvest details
    pick_method: Optional[str] = Field(None, max_length=20, description="Updated pick method")
    pick_start_time: Optional[str] = Field(None, max_length=8, description="Updated start time")
    pick_end_time: Optional[str] = Field(None, max_length=8, description="Updated end time")
    bins_count: Optional[int] = Field(None, ge=0, description="Updated bins count")
    field_temp_c: Optional[float] = Field(None, ge=-50, le=60, description="Updated field temperature")
    notes: Optional[str] = Field(None, max_length=255, description="Updated notes")
    
    @field_validator('code')
    @classmethod
    def code_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate code format and auto-uppercase."""
        if v is not None:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Code must be alphanumeric (hyphens and underscores allowed)')
            return v.upper()
        return v
    
    @field_validator('pick_method')
    @classmethod
    def pick_method_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate pick method is hand or machine."""
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ['hand', 'machine']:
                raise ValueError("Pick method must be 'hand' or 'machine'")
            return v_lower
        return v
    
    @field_validator('pick_start_time', 'pick_end_time')
    @classmethod
    def time_must_be_valid_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format HH:MM or HH:MM:SS."""
        if v is not None:
            try:
                if len(v) == 5:  # HH:MM
                    time.fromisoformat(v + ':00')
                elif len(v) == 8:  # HH:MM:SS
                    time.fromisoformat(v)
                else:
                    raise ValueError('Time must be in HH:MM or HH:MM:SS format')
            except ValueError as e:
                raise ValueError(f'Invalid time format: {e}')
        return v


class HarvestLotListFilters(BaseModel):
    """
    Query parameters for listing harvest lots.
    
    Supports filtering by vineyard, block, date range, and soft-deleted status.
    """
    vineyard_id: Optional[int] = Field(None, gt=0, description="Filter by vineyard ID")
    block_id: Optional[int] = Field(None, gt=0, description="Filter by block ID")
    harvest_date_from: Optional[date] = Field(None, description="Filter lots harvested on or after this date")
    harvest_date_to: Optional[date] = Field(None, description="Filter lots harvested on or before this date")
    include_deleted: bool = Field(False, description="Include soft-deleted harvest lots")
    
    @field_validator('harvest_date_to')
    @classmethod
    def date_to_must_be_after_date_from(cls, v: Optional[date], info) -> Optional[date]:
        """Validate date range if both dates provided."""
        if v is not None and 'harvest_date_from' in info.data:
            date_from = info.data['harvest_date_from']
            if date_from is not None and v < date_from:
                raise ValueError('harvest_date_to must be >= harvest_date_from')
        return v
