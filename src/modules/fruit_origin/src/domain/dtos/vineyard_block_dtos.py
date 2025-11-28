"""Data Transfer Objects for VineyardBlock entity."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class VineyardBlockCreate:
    """DTO for creating a new vineyard block."""

    code: str
    soil_type: Optional[str] = None
    slope_pct: Optional[float] = None
    aspect_deg: Optional[float] = None
    area_ha: Optional[float] = None
    elevation_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    irrigation: Optional[bool] = None
    organic_certified: Optional[bool] = None


@dataclass
class VineyardBlockUpdate:
    """DTO for updating a vineyard block."""

    code: Optional[str] = None
    soil_type: Optional[str] = None
    slope_pct: Optional[float] = None
    aspect_deg: Optional[float] = None
    area_ha: Optional[float] = None
    elevation_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    irrigation: Optional[bool] = None
    organic_certified: Optional[bool] = None
