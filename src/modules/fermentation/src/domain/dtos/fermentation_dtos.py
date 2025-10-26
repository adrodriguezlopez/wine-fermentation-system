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
