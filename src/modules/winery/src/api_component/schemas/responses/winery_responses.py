"""
Response DTOs for Winery API endpoints.

Following Pydantic v2 patterns for response serialization.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from src.modules.winery.src.domain.entities.winery import Winery


class WineryResponse(BaseModel):
    """Response DTO for a single winery."""
    
    id: int = Field(..., description="Winery ID")
    code: str = Field(..., description="Unique winery code")
    name: str = Field(..., description="Winery name")
    location: Optional[str] = Field(None, description="Winery location")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_entity(cls, entity: Winery) -> "WineryResponse":
        """Create response DTO from domain entity."""
        return cls(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            location=entity.location,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class PaginatedWineriesResponse(BaseModel):
    """Response DTO for paginated list of wineries."""
    
    items: List[WineryResponse] = Field(..., description="List of wineries")
    total: int = Field(..., description="Total count of wineries")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset for pagination")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": 1,
                            "code": "WINERY-001",
                            "name": "Napa Valley Winery",
                            "location": "Napa, CA",
                            "notes": "Premium wines",
                            "created_at": "2024-01-01T00:00:00",
                            "updated_at": "2024-01-01T00:00:00"
                        }
                    ],
                    "total": 1,
                    "limit": 10,
                    "offset": 0
                }
            ]
        }
    }
