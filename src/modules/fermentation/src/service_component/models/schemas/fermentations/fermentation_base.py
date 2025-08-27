from datetime import datetime
from pydantic import BaseModel, Field


class FermentationBase(BaseModel):
    """Base schema with common fermentation fields"""

    vintage_year: int = Field(..., ge=1900, le=2100, description="Vintage year")
    winery: str = Field(..., min_length=1, max_length=100, description="Winery name")
    vineyard: str = Field(
        ..., min_length=1, max_length=100, description="Vineyard name"
    )
    grape_variety: str = Field(
        ..., min_length=1, max_length=100, description="Grape variety"
    )
    yeast_strain: str = Field(
        ..., min_length=1, max_length=100, description="Yeast strain"
    )
    initial_fruit_quantity_kg: float = Field(
        ..., gt=0, description="Initial fruit quantity in kg"
    )
    initial_sugar_brix: float = Field(
        ..., gt=0, description="Initial sugar content in Brix"
    )
    initial_density: float = Field(..., gt=0, description="Initial specific gravity")
    start_date: datetime = Field(..., description="Fermentation start date")
