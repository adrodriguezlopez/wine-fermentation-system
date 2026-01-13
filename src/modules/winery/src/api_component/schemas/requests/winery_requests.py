"""
Request DTOs for Winery API endpoints.

Following Pydantic v2 patterns for request validation.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class WineryCreateRequest(BaseModel):
    """Request DTO for creating a new winery."""
    
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique winery code (alphanumeric, hyphens, underscores only)",
        examples=["WINERY-001", "NAPA-VALLEY-2024"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Winery name",
        examples=["Napa Valley Winery", "Sonoma Vineyards"]
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="Winery location or address",
        examples=["123 Wine Road, Napa Valley, CA 94558"]
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the winery",
        examples=["Founded in 1980, specializes in Cabernet Sauvignon"]
    )
    
    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate code format: alphanumeric, hyphens, underscores only."""
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError(
                "Code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v.upper()  # Normalize to uppercase
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "WINERY-001",
                    "name": "Napa Valley Winery",
                    "location": "Napa Valley, CA",
                    "notes": "Premium wine producer"
                }
            ]
        }
    }


class WineryUpdateRequest(BaseModel):
    """Request DTO for updating an existing winery.
    
    Note: Code is immutable and cannot be updated.
    """
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated winery name"
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated winery location"
    )
    notes: Optional[str] = Field(
        None,
        description="Updated notes"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Winery Name",
                    "location": "New Location",
                    "notes": "Updated notes"
                }
            ]
        }
    }
