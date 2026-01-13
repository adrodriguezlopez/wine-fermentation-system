"""
Request DTOs for Historical Data API endpoints.

Following Pydantic v2 patterns for request validation.
Related ADR: ADR-032 (Historical Data API Layer)
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class HistoricalFermentationQueryRequest(BaseModel):
    """Request DTO for querying historical fermentations with filters."""
    
    start_date_from: Optional[date] = Field(
        None,
        description="Filter by start date (inclusive)",
        examples=["2024-01-01"]
    )
    start_date_to: Optional[date] = Field(
        None,
        description="Filter by start date (inclusive)",
        examples=["2024-12-31"]
    )
    fruit_origin_id: Optional[int] = Field(
        None,
        description="Filter by fruit origin ID",
        examples=[5]
    )
    status: Optional[str] = Field(
        None,
        description="Filter by fermentation status",
        examples=["completed", "stuck", "in_progress"]
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of results",
        examples=[100]
    )
    offset: int = Field(
        0,
        ge=0,
        description="Offset for pagination",
        examples=[0]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "start_date_from": "2024-01-01",
                    "start_date_to": "2024-12-31",
                    "fruit_origin_id": 5,
                    "status": "completed",
                    "limit": 100,
                    "offset": 0
                }
            ]
        }
    }


class PatternExtractionRequest(BaseModel):
    """Request DTO for extracting patterns from historical data."""
    
    fruit_origin_id: Optional[int] = Field(
        None,
        description="Filter by fruit origin ID for pattern extraction",
        examples=[5]
    )
    start_date: Optional[date] = Field(
        None,
        description="Start date for pattern extraction range",
        examples=["2024-01-01"]
    )
    end_date: Optional[date] = Field(
        None,
        description="End date for pattern extraction range",
        examples=["2024-12-31"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fruit_origin_id": 5,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            ]
        }
    }
