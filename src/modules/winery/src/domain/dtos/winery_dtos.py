"""
Winery Data Transfer Objects.

DTOs for winery creation and update operations.
Following ADR-016: Winery Service Layer Architecture.
Simplified pattern matching Fruit Origin (ADR-014).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WineryCreate:
    """DTO for creating a new winery."""

    code: str
    name: str
    location: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class WineryUpdate:
    """DTO for updating a winery."""

    name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    # Code is immutable - cannot be updated after creation

