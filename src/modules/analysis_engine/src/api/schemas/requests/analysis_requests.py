"""
Request schemas for Analysis Engine API endpoints.

Pydantic models that validate incoming HTTP request data before
it reaches the service layer. Following ADR-006 API Layer Design.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DensityReadingRequest(BaseModel):
    """A single density reading with timestamp."""
    timestamp: datetime = Field(..., description="When the reading was taken (UTC)")
    density: float = Field(..., description="Density value in g/L", gt=0, lt=2000)


class AnalysisCreateRequest(BaseModel):
    """
    Request body for triggering a fermentation analysis.

    The analysis engine uses current sensor readings alongside
    historical data to detect anomalies and generate recommendations.
    """

    fermentation_id: UUID = Field(
        ...,
        description="UUID of the fermentation to analyze"
    )
    current_density: float = Field(
        ...,
        description="Current density reading in g/L (typical range 990-1120)",
        gt=900,
        lt=1200
    )
    temperature_celsius: float = Field(
        ...,
        description="Current fermentation temperature in °C (typical range 5-45)",
        ge=-10,
        le=60
    )
    variety: str = Field(
        ...,
        description="Grape variety (e.g., 'Cabernet Sauvignon', 'Pinot Noir')",
        min_length=2,
        max_length=100
    )
    fruit_origin_id: Optional[UUID] = Field(
        None,
        description="UUID of the fruit origin (for historical comparison filtering)"
    )
    starting_brix: Optional[float] = Field(
        None,
        description="Starting Brix at fermentation start (for similarity matching)",
        ge=0,
        le=40
    )
    days_fermenting: float = Field(
        default=0.0,
        description="Days since fermentation started",
        ge=0,
        le=365
    )
    previous_densities: Optional[List[DensityReadingRequest]] = Field(
        None,
        description="Historical density readings for trend analysis (chronological order)"
    )

    @field_validator("variety")
    @classmethod
    def validate_variety(cls, v: str) -> str:
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "fermentation_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_density": 1050.5,
                "temperature_celsius": 22.0,
                "variety": "Cabernet Sauvignon",
                "fruit_origin_id": None,
                "starting_brix": 24.0,
                "days_fermenting": 5.0,
                "previous_densities": [
                    {"timestamp": "2024-01-01T08:00:00Z", "density": 1080.0},
                    {"timestamp": "2024-01-02T08:00:00Z", "density": 1065.0},
                    {"timestamp": "2024-01-03T08:00:00Z", "density": 1050.5}
                ]
            }
        }
    }


class RecommendationApplyRequest(BaseModel):
    """
    Request body for marking a recommendation as applied.

    The winemaker confirms they've applied the recommendation
    so the system can track effectiveness.
    """

    notes: Optional[str] = Field(
        None,
        description="Optional notes from the winemaker about how/when the recommendation was applied",
        max_length=1000
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "notes": "Added 50g/hL DAP to fermentation tank. Applied at 14:30."
            }
        }
    }
