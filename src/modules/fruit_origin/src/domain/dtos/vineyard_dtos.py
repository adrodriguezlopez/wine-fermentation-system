"""Data Transfer Objects for Vineyard entity."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class VineyardCreate:
    """DTO for creating a new vineyard."""

    code: str
    name: str
    notes: Optional[str] = None


@dataclass
class VineyardUpdate:
    """DTO for updating a vineyard."""

    code: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
