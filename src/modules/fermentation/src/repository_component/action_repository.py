"""
ActionRepository — SQLAlchemy AsyncSession implementation (ADR-041).
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.winemaker_action import (
    WinemakerAction,
)
from src.modules.fermentation.src.domain.repositories.action_repository_interface import (
    IActionRepository,
)


class ActionRepository(IActionRepository):
    """Concrete repository for WinemakerAction using an injected AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, action: WinemakerAction) -> WinemakerAction:
        self.session.add(action)
        await self.session.flush()
        return action

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(
        self, action_id: int, winery_id: int
    ) -> Optional[WinemakerAction]:
        stmt = select(WinemakerAction).where(
            WinemakerAction.id == action_id,
            WinemakerAction.winery_id == winery_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        base = and_(
            WinemakerAction.fermentation_id == fermentation_id,
            WinemakerAction.winery_id == winery_id,
        )
        count_stmt = select(func.count()).select_from(WinemakerAction).where(base)
        items_stmt = (
            select(WinemakerAction)
            .where(base)
            .order_by(WinemakerAction.taken_at.desc())
            .offset(skip)
            .limit(limit)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, total

    async def list_by_execution(
        self,
        execution_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        base = and_(
            WinemakerAction.execution_id == execution_id,
            WinemakerAction.winery_id == winery_id,
        )
        count_stmt = select(func.count()).select_from(WinemakerAction).where(base)
        items_stmt = (
            select(WinemakerAction)
            .where(base)
            .order_by(WinemakerAction.taken_at.desc())
            .offset(skip)
            .limit(limit)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, total

    async def list_by_alert(
        self, alert_id: int, winery_id: int
    ) -> List[WinemakerAction]:
        stmt = (
            select(WinemakerAction)
            .where(
                WinemakerAction.alert_id == alert_id,
                WinemakerAction.winery_id == winery_id,
            )
            .order_by(WinemakerAction.taken_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_outcome(
        self,
        action_id: int,
        winery_id: int,
        outcome: str,
        outcome_notes: Optional[str],
    ) -> Optional[WinemakerAction]:
        action = await self.get_by_id(action_id, winery_id)
        if action is None:
            return None
        action.outcome = outcome
        action.outcome_notes = outcome_notes
        action.outcome_recorded_at = datetime.utcnow()
        action.updated_at = datetime.utcnow()
        await self.session.flush()
        return action

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, action_id: int, winery_id: int) -> bool:
        action = await self.get_by_id(action_id, winery_id)
        if action is None:
            return False
        await self.session.delete(action)
        await self.session.flush()
        return True
