"""
Fermentation Data Transfer Objects.

Pure Python dataclasses for fermentation data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
