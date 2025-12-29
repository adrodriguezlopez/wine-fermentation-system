"""
Harvest Lot Response DTOs for API Layer.

Pydantic v2 models for serializing harvest lot API responses.
Converts domain entities to JSON-serializable formats.

Related ADRs:
- ADR-015: Fruit Origin API Design
- ADR-001: Fruit Origin Model
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional, List


class HarvestLotResponse(BaseModel):
    """
    Response DTO for harvest lot entity.
    
    Contains all harvest lot fields including timestamps and relationships.
    Used for single lot responses (GET by ID, POST, PATCH).
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Identity
    id: int = Field(..., description="Harvest lot ID")
    winery_id: int = Field(..., description="Winery ID (multi-tenancy)")
    block_id: int = Field(..., description="Vineyard block ID")
    code: str = Field(..., description="Unique harvest lot code")
    
    # Core harvest data
    harvest_date: date = Field(..., description="Date fruit was harvested")
    weight_kg: float = Field(..., description="Total weight in kilograms")
    
    # Brix measurements
    brix_at_harvest: Optional[float] = Field(None, description="Sugar content in Brix")
    brix_method: Optional[str] = Field(None, description="Measurement method")
    brix_measured_at: Optional[str] = Field(None, description="Measurement location/timestamp")
    
    # Grape details
    grape_variety: Optional[str] = Field(None, description="Grape variety")
    clone: Optional[str] = Field(None, description="Clone identifier")
    rootstock: Optional[str] = Field(None, description="Rootstock type")
    
    # Harvest details
    pick_method: Optional[str] = Field(None, description="Picking method (hand/machine)")
    pick_start_time: Optional[str] = Field(None, description="Pick start time")
    pick_end_time: Optional[str] = Field(None, description="Pick end time")
    bins_count: Optional[int] = Field(None, description="Number of bins")
    field_temp_c: Optional[float] = Field(None, description="Field temperature in Celsius")
    notes: Optional[str] = Field(None, description="General notes")
    
    # Metadata
    is_deleted: bool = Field(..., description="Soft delete flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Optional computed/joined fields
    vineyard_name: Optional[str] = Field(None, description="Vineyard name (via block)")
    vineyard_code: Optional[str] = Field(None, description="Vineyard code (via block)")
    block_name: Optional[str] = Field(None, description="Block name")
    used_in_fermentation: Optional[bool] = Field(None, description="Whether lot is used in any fermentation")


class HarvestLotListResponse(BaseModel):
    """
    Response DTO for harvest lot list endpoint.
    
    Contains paginated list of harvest lots with metadata.
    Used for GET /api/v1/harvest-lots endpoint.
    """
    total: int = Field(..., description="Total number of harvest lots matching filters")
    lots: List[HarvestLotResponse] = Field(..., description="List of harvest lots")
    
    # Optional pagination metadata (future enhancement)
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


class HarvestLotUsageResponse(BaseModel):
    """
    Response DTO for harvest lot usage check endpoint.
    
    Indicates whether a harvest lot is used in any fermentations.
    Used for GET /api/v1/harvest-lots/{id}/usage endpoint.
    """
    lot_id: int = Field(..., description="Harvest lot ID")
    lot_code: str = Field(..., description="Harvest lot code")
    is_used: bool = Field(..., description="True if lot is used in any fermentation")
    fermentation_count: int = Field(..., description="Number of fermentations using this lot")
    fermentation_ids: List[int] = Field(default_factory=list, description="List of fermentation IDs using this lot")
    can_delete: bool = Field(..., description="True if lot can be safely deleted (not used)")
