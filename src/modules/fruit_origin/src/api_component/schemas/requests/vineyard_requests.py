"""
Vineyard Request DTOs (Pydantic v2)

Request schemas for vineyard API endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class VineyardCreateRequest(BaseModel):
    """Request DTO for creating a vineyard."""
    
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique vineyard code within winery",
        examples=["VYD-001", "NORTH_BLOCK"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Vineyard name",
        examples=["Northern Vineyard", "Hillside Estate"]
    )
    notes: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional notes about the vineyard"
    )
    
    @field_validator('code')
    @classmethod
    def code_must_be_alphanumeric(cls, v: str) -> str:
        """Validate code format (alphanumeric with hyphens/underscores)."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "VYD-001",
                    "name": "Northern Vineyard",
                    "notes": "Main production vineyard with 5 blocks"
                }
            ]
        }
    }


class VineyardUpdateRequest(BaseModel):
    """Request DTO for updating a vineyard."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated vineyard name"
    )
    notes: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated notes"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Northern Vineyard - Extended",
                    "notes": "Expanded to 7 blocks in 2025"
                }
            ]
        }
    }


class VineyardListFilters(BaseModel):
    """Query parameters for vineyard list endpoint."""
    
    include_deleted: bool = Field(
        False,
        description="Include soft-deleted vineyards in results"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"include_deleted": False},
                {"include_deleted": True}
            ]
        }
    }
