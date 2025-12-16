"""
Winery Data Transfer Objects.

DTOs for winery creation and update operations.
Following ADR-009: Phase 3 - Winery Repository Implementation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WineryCreate:
    """
    DTO for creating a new winery.
    
    Attributes:
        name: Winery name (required, max 200 chars)
        region: Geographic region (optional, max 100 chars)
    """
    name: str
    region: Optional[str] = None

    def __post_init__(self):
        """Validate winery creation data."""
        if not self.name or not self.name.strip():
            raise ValueError("Winery name is required")
        
        if len(self.name) > 200:
            raise ValueError("Winery name cannot exceed 200 characters")
        
        if self.region is not None and len(self.region) > 100:
            raise ValueError("Region cannot exceed 100 characters")
        
        # Strip whitespace
        self.name = self.name.strip()
        if self.region:
            self.region = self.region.strip()


@dataclass
class WineryUpdate:
    """
    DTO for updating winery information.
    
    All fields are optional for partial updates.
    
    Attributes:
        name: Updated winery name (optional, max 200 chars)
        region: Updated geographic region (optional, max 100 chars)
    """
    name: Optional[str] = None
    region: Optional[str] = None

    def __post_init__(self):
        """Validate winery update data."""
        if self.name is not None:
            if not self.name.strip():
                raise ValueError("Winery name cannot be empty")
            
            if len(self.name) > 200:
                raise ValueError("Winery name cannot exceed 200 characters")
            
            self.name = self.name.strip()
        
        if self.region is not None:
            if len(self.region) > 100:
                raise ValueError("Region cannot exceed 100 characters")
            
            self.region = self.region.strip()

    def has_updates(self) -> bool:
        """
        Check if this DTO contains any updates.
        
        Returns:
            bool: True if at least one field is set
        """
        return self.name is not None or self.region is not None
