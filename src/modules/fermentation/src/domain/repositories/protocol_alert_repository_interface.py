"""
Repository Interface for ProtocolAlert (ADR-040).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert


class IProtocolAlertRepository(ABC):
    """Abstract repository for ProtocolAlert persistence operations."""

    @abstractmethod
    async def create(self, alert: ProtocolAlert) -> ProtocolAlert:
        """Persist a new alert."""
        pass

    @abstractmethod
    async def create_many(self, alerts: List[ProtocolAlert]) -> List[ProtocolAlert]:
        """Persist multiple alerts in one flush."""
        pass

    @abstractmethod
    async def get_by_id(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Get alert by primary key."""
        pass

    @abstractmethod
    async def get_by_execution(
        self,
        execution_id: int,
        status: Optional[str] = None,
        alert_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAlert]:
        """
        List alerts for an execution, optionally filtered by status/type.
        Returns newest-first.
        """
        pass

    @abstractmethod
    async def get_pending_by_winery(
        self,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAlert]:
        """List all PENDING alerts across all executions for a winery."""
        pass

    @abstractmethod
    async def acknowledge(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Set status=ACKNOWLEDGED and acknowledged_at=now."""
        pass

    @abstractmethod
    async def dismiss(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Set status=DISMISSED and dismissed_at=now."""
        pass

    @abstractmethod
    async def count_pending(self, execution_id: int) -> int:
        """Count PENDING alerts for an execution."""
        pass
