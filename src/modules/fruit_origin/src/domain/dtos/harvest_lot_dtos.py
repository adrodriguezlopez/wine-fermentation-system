"""
Harvest Lot Data Transfer Objects.

Pure Python dataclasses for harvest lot data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).

Related ADRs:
- ADR-001: Fruit Origin Model
- ADR-009: Missing Repositories Implementation
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class HarvestLotCreate:
    """
    Data transfer object for creating new harvest lots.
    
    Contains all required and optional fields for harvest lot creation.
    Used by repository layer to create new harvest lot records.
    
    Attributes:
        block_id: ID of the vineyard block where fruit was harvested
        code: Unique code for this harvest lot (unique per winery)
        harvest_date: Date when fruit was harvested
        weight_kg: Total weight of harvested fruit in kilograms
        brix_at_harvest: Optional sugar content in Brix at harvest time
        brix_method: Optional method used to measure Brix (e.g., 'refractometer', 'hydrometer')
        brix_measured_at: Optional location where Brix was measured (e.g., 'field', 'receival')
        grape_variety: Optional grape variety name (e.g., 'Chardonnay', 'Pinot Noir')
        clone: Optional clone identifier (e.g., 'Clone 95', 'Dijon 115')
        rootstock: Optional rootstock type (e.g., '101-14', '3309C')
        pick_method: Optional picking method (e.g., 'hand', 'machine')
        pick_start_time: Optional timestamp when picking started
        pick_end_time: Optional timestamp when picking ended
        bins_count: Optional number of bins/containers used
        field_temp_c: Optional field temperature in Celsius at harvest
        notes: Optional general notes about this harvest lot
    
    Business Rules:
        - code must be unique per winery (enforced by unique constraint)
        - block_id must exist and belong to same winery
        - weight_kg must be positive
        - harvest_date should be <= current date (validated at service layer)
    """
    block_id: int
    code: str
    harvest_date: date
    weight_kg: float
    brix_at_harvest: Optional[float] = None
    brix_method: Optional[str] = None
    brix_measured_at: Optional[str] = None
    grape_variety: Optional[str] = None
    clone: Optional[str] = None
    rootstock: Optional[str] = None
    pick_method: Optional[str] = None
    pick_start_time: Optional[datetime] = None
    pick_end_time: Optional[datetime] = None
    bins_count: Optional[int] = None
    field_temp_c: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class HarvestLotUpdate:
    """
    Data transfer object for updating existing harvest lots.
    
    All fields are optional to support partial updates.
    Only provided (non-None) fields will be updated.
    
    Attributes:
        code: Updated harvest lot code (must remain unique per winery)
        harvest_date: Updated harvest date
        weight_kg: Updated total weight
        brix_at_harvest: Updated Brix measurement
        brix_method: Updated Brix measurement method
        brix_measured_at: Updated Brix measurement location
        grape_variety: Updated grape variety
        clone: Updated clone identifier
        rootstock: Updated rootstock type
        pick_method: Updated picking method
        pick_start_time: Updated picking start time
        pick_end_time: Updated picking end time
        bins_count: Updated bins count
        field_temp_c: Updated field temperature
        notes: Updated notes
    
    Note:
        - block_id and winery_id cannot be updated (immutable after creation)
        - Changing code requires uniqueness validation
        - Cannot update if lot is used in any fermentation (business rule)
    """
    code: Optional[str] = None
    harvest_date: Optional[date] = None
    weight_kg: Optional[float] = None
    brix_at_harvest: Optional[float] = None
    brix_method: Optional[str] = None
    brix_measured_at: Optional[str] = None
    grape_variety: Optional[str] = None
    clone: Optional[str] = None
    rootstock: Optional[str] = None
    pick_method: Optional[str] = None
    pick_start_time: Optional[datetime] = None
    pick_end_time: Optional[datetime] = None
    bins_count: Optional[int] = None
    field_temp_c: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class HarvestLotSummary:
    """
    Data transfer object for harvest lot summary information.
    
    Lightweight version of HarvestLot for list views and reports.
    Contains only essential fields for display purposes.
    
    Attributes:
        id: Harvest lot ID
        code: Harvest lot code
        harvest_date: Date of harvest
        weight_kg: Total weight harvested
        grape_variety: Grape variety (if known)
        block_code: Code of the vineyard block
        vineyard_name: Name of the vineyard
        brix_at_harvest: Brix measurement (if available)
        is_fully_used: Whether all fruit has been used in fermentations
    
    Use Cases:
        - List views (harvest lot index)
        - Reports and exports
        - Search results
        - API responses for list endpoints
    """
    id: int
    code: str
    harvest_date: date
    weight_kg: float
    grape_variety: Optional[str]
    block_code: str
    vineyard_name: str
    brix_at_harvest: Optional[float]
    is_fully_used: bool
