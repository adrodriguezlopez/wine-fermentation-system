"""
Vineyard Response DTOs (Pydantic v2)

Response schemas for vineyard API endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class VineyardResponse(BaseModel):
    """Response DTO for vineyard entity."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Vineyard ID")
    winery_id: int = Field(..., description="Owner winery ID")
    code: str = Field(..., description="Vineyard code")
    name: str = Field(..., description="Vineyard name")
    notes: Optional[str] = Field(None, description="Optional notes")
    is_deleted: bool = Field(..., description="Soft delete flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Optional computed fields (can be populated by service)
    blocks_count: Optional[int] = Field(
        None,
        description="Number of blocks in this vineyard"
    )


class VineyardListResponse(BaseModel):
    """Response DTO for vineyard list endpoint."""
    
    vineyards: list[VineyardResponse] = Field(
        ...,
        description="List of vineyards"
    )
    total: int = Field(
        ...,
        description="Total number of vineyards"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "vineyards": [
                        {
                            "id": 1,
                            "winery_id": 1,
                            "code": "VYD-001",
                            "name": "Northern Vineyard",
                            "notes": "Main production area",
                            "is_deleted": False,
                            "created_at": "2025-01-15T10:00:00Z",
                            "updated_at": "2025-01-15T10:00:00Z",
                            "blocks_count": 5
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }
