"""
Fermentation Data Transfer Objects.

Pure Python dataclasses for fermentation data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


@dataclass
class FermentationCreate:
    """
    Data transfer object for creating new fermentations.
    
    Contains all required fields for fermentation creation.
    Used by repository layer to create new fermentation records.
    
    Attributes:
        fermented_by_user_id: ID of user creating the fermentation (from auth context)
        vintage_year: Year of the vintage
        yeast_strain: Yeast strain identifier
        input_mass_kg: Input mass in kilograms
        initial_sugar_brix: Initial sugar content in Brix
        initial_density: Initial specific gravity
        vessel_code: Optional vessel/tank identifier
        start_date: Fermentation start date (defaults to now if not provided)
    """
    fermented_by_user_id: int
    vintage_year: int
    yeast_strain: str
    input_mass_kg: float
    initial_sugar_brix: float
    initial_density: float
    vessel_code: Optional[str] = None
    start_date: Optional[datetime] = None


@dataclass
class FermentationUpdate:
    """
    Data transfer object for updating existing fermentations.
    
    All fields are optional to support partial updates.
    Only provided (non-None) fields will be updated.
    
    Attributes:
        yeast_strain: Updated yeast strain identifier
        vessel_code: Updated vessel/tank identifier
        input_mass_kg: Updated input mass in kilograms
        initial_sugar_brix: Updated initial sugar content in Brix
        initial_density: Updated initial specific gravity
        vintage_year: Updated vintage year
        start_date: Updated fermentation start date
    """
    yeast_strain: Optional[str] = None
    vessel_code: Optional[str] = None
    input_mass_kg: Optional[float] = None
    initial_sugar_brix: Optional[float] = None
    initial_density: Optional[float] = None
    vintage_year: Optional[int] = None
    start_date: Optional[datetime] = None


@dataclass
class LotSourceData:
    """
    Data transfer object for harvest lot source in blend creation.
    
    Represents a single harvest lot contributing to a fermentation blend.
    Multiple LotSourceData instances combine to create a fermentation from
    multiple vineyard sources (ADR-001 fruit origin model).
    
    Attributes:
        harvest_lot_id: ID of the harvest lot being used
        mass_used_kg: Mass in kilograms taken from this lot
        notes: Optional notes about this lot's contribution
    
    Business Rules:
        - mass_used_kg must be > 0
        - mass_used_kg cannot exceed harvest lot's available mass
        - Sum of all lot masses should equal fermentation input_mass_kg
    
    Example:
        ```python
        # Blend from 3 vineyard blocks
        lot1 = LotSourceData(harvest_lot_id=1, mass_used_kg=50.0)
        lot2 = LotSourceData(harvest_lot_id=2, mass_used_kg=30.0)
        lot3 = LotSourceData(harvest_lot_id=3, mass_used_kg=20.0)
        # Total: 100kg fermentation
        ```
    """
    harvest_lot_id: int
    mass_used_kg: Decimal
    notes: Optional[str] = None


@dataclass
class FermentationWithBlendCreate:
    """
    Data transfer object for creating fermentation with blend (multiple lot sources).
    
    Combines fermentation data with harvest lot sources for atomic creation.
    This ensures a fermentation and its lot sources are created together or not at all.
    
    Use Case: Creating wine blends from multiple vineyard blocks/lots (ADR-001).
    
    Attributes:
        fermentation_data: Base fermentation creation data
        lot_sources: List of harvest lots contributing to this fermentation
    
    Business Rules:
        - At least one lot source required (len(lot_sources) >= 1)
        - Sum of lot_sources masses should equal fermentation_data.input_mass_kg
        - All harvest_lot_ids must exist and belong to same winery
        - Each lot can only be used once per fermentation
    
    Validation:
        - Performed by FermentationValidator
        - Checks lot availability, mass consistency, vineyard access
    
    Example:
        ```python
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="EC-1118",
            input_mass_kg=100.0,
            initial_sugar_brix=22.5,
            initial_density=1.095
        )
        
        lot_sources = [
            LotSourceData(harvest_lot_id=1, mass_used_kg=Decimal("60.0")),
            LotSourceData(harvest_lot_id=2, mass_used_kg=Decimal("40.0"))
        ]
        
        blend = FermentationWithBlendCreate(
            fermentation_data=fermentation_data,
            lot_sources=lot_sources
        )
        ```
    """
    fermentation_data: FermentationCreate
    lot_sources: List[LotSourceData]
