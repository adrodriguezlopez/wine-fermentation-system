"""
ProtocolAlert Repository Implementation (ADR-040).

Concrete implementation using SQLAlchemy AsyncSession directly,
following the fermentation module pattern (not BaseRepository).
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.domain.repositories.protocol_alert_repository_interface import (
    IProtocolAlertRepository,
)


class ProtocolAlertRepository(IProtocolAlertRepository):
    """Repository for ProtocolAlert persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, alert: ProtocolAlert) -> ProtocolAlert:
        """Persist a new alert."""
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def create_many(self, alerts: List[ProtocolAlert]) -> List[ProtocolAlert]:
        """Persist multiple alerts in one flush."""
        if not alerts:
            return []
        for alert in alerts:
            self.session.add(alert)
        await self.session.flush()
        return alerts

    async def get_by_id(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Get alert by primary key."""
        stmt = select(ProtocolAlert).where(ProtocolAlert.id == alert_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_execution(
        self,
        execution_id: int,
        status: Optional[str] = None,
        alert_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAlert]:
        """List alerts for an execution, optionally filtered by status/type, newest-first."""
        conditions = [ProtocolAlert.execution_id == execution_id]
        if status is not None:
            conditions.append(ProtocolAlert.status == status)
        if alert_type is not None:
            conditions.append(ProtocolAlert.alert_type == alert_type)

        stmt = (
            select(ProtocolAlert)
            .where(and_(*conditions))
            .order_by(ProtocolAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_by_winery(
        self,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProtocolAlert]:
        """List PENDING alerts across all executions for a winery, newest-first."""
        stmt = (
            select(ProtocolAlert)
            .where(
                and_(
                    ProtocolAlert.winery_id == winery_id,
                    ProtocolAlert.status == "PENDING",
                )
            )
            .order_by(ProtocolAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def acknowledge(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Set status=ACKNOWLEDGED and acknowledged_at=now."""
        alert = await self.get_by_id(alert_id)
        if alert is None:
            return None
        alert.acknowledge()
        await self.session.flush()
        return alert

    async def dismiss(self, alert_id: int) -> Optional[ProtocolAlert]:
        """Set status=DISMISSED and dismissed_at=now."""
        alert = await self.get_by_id(alert_id)
        if alert is None:
            return None
        alert.dismiss()
        await self.session.flush()
        return alert

    async def count_pending(self, execution_id: int) -> int:
        """Count PENDING alerts for an execution."""
        stmt = select(func.count(ProtocolAlert.id)).where(
            and_(
                ProtocolAlert.execution_id == execution_id,
                ProtocolAlert.status == "PENDING",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
