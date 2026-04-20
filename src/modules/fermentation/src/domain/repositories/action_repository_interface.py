"""
Repository Interface for WinemakerAction (ADR-041).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from src.modules.fermentation.src.domain.entities.winemaker_action import (
    WinemakerAction,
)


class IActionRepository(ABC):
    """Abstract repository for WinemakerAction persistence operations."""

    @abstractmethod
    async def create(self, action: WinemakerAction) -> WinemakerAction:
        """Persist a new action."""
        pass

    @abstractmethod
    async def get_by_id(
        self, action_id: int, winery_id: int
    ) -> Optional[WinemakerAction]:
        """Get action by PK, scoped to winery. Returns None if not found."""
        pass

    @abstractmethod
    async def list_by_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        """Return (items, total_count) for a fermentation, newest-first."""
        pass

    @abstractmethod
    async def list_by_execution(
        self,
        execution_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        """Return (items, total_count) for a protocol execution, newest-first."""
        pass

    @abstractmethod
    async def list_by_alert(
        self, alert_id: int, winery_id: int
    ) -> List[WinemakerAction]:
        """All actions linked to a specific alert."""
        pass

    @abstractmethod
    async def update_outcome(
        self,
        action_id: int,
        winery_id: int,
        outcome: str,
        outcome_notes: Optional[str],
    ) -> Optional[WinemakerAction]:
        """Update outcome fields. Returns updated entity or None if not found."""
        pass

    @abstractmethod
    async def delete(self, action_id: int, winery_id: int) -> bool:
        """Hard-delete. Returns True if deleted, False if not found."""
        pass
