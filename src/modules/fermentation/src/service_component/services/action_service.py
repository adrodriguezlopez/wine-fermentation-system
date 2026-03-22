"""
ActionService — orchestration service for WinemakerAction (ADR-041).

Responsibilities:
  - record_action: validate ownership, persist, auto-acknowledge linked alert
  - update_outcome: record post-action observation
  - get_actions_for_fermentation / get_actions_for_execution: paginated queries
  - get_action / delete_action: single-item access
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.winemaker_action import WinemakerAction
from src.modules.fermentation.src.domain.enums.step_type import ActionOutcome
from src.modules.fermentation.src.repository_component.action_repository import ActionRepository
from src.modules.fermentation.src.repository_component.protocol_alert_repository import (
    ProtocolAlertRepository,
)
from src.shared.wine_fermentator_logging import get_logger

logger = get_logger(__name__)


class ActionNotFoundError(Exception):
    """Raised when an action cannot be found or does not belong to the winery."""


class ActionService:
    """
    Service layer for winemaker action tracking.

    Accepts an AsyncSession and builds its own repository instances, following
    the same pattern as ProtocolAlertService and other fermentation services.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ActionRepository(session)
        self._alert_repo = ProtocolAlertRepository(session)

    # ------------------------------------------------------------------
    # Command: record a new action
    # ------------------------------------------------------------------

    async def record_action(
        self,
        winery_id: int,
        taken_by_user_id: int,
        action_type: str,
        description: str,
        taken_at: datetime,
        fermentation_id: Optional[int] = None,
        execution_id: Optional[int] = None,
        step_id: Optional[int] = None,
        alert_id: Optional[int] = None,
        recommendation_id: Optional[int] = None,
    ) -> WinemakerAction:
        """
        Persist a new winemaker action.

        Side-effect: if alert_id is provided, the referenced alert is
        automatically acknowledged (PENDING → ACKNOWLEDGED).
        """
        action = WinemakerAction(
            winery_id=winery_id,
            taken_by_user_id=taken_by_user_id,
            action_type=action_type,
            description=description,
            taken_at=taken_at,
            fermentation_id=fermentation_id,
            execution_id=execution_id,
            step_id=step_id,
            alert_id=alert_id,
            recommendation_id=recommendation_id,
            outcome=ActionOutcome.PENDING.value,
        )
        action = await self._repo.create(action)

        # Auto-acknowledge the linked alert so it disappears from the queue
        if alert_id is not None:
            await self._alert_repo.acknowledge(alert_id)
            logger.info(
                "action_recorded_alert_acknowledged",
                action_id=action.id,
                alert_id=alert_id,
                winery_id=winery_id,
            )
        else:
            logger.info(
                "action_recorded",
                action_id=action.id,
                action_type=action_type,
                winery_id=winery_id,
            )

        return action

    # ------------------------------------------------------------------
    # Command: update outcome
    # ------------------------------------------------------------------

    async def update_outcome(
        self,
        action_id: int,
        winery_id: int,
        outcome: str,
        outcome_notes: Optional[str] = None,
    ) -> WinemakerAction:
        """
        Record the winemaker's post-action observation.

        Raises:
            ActionNotFoundError: action not found or belongs to another winery.
            ValueError: outcome is not a valid ActionOutcome value.
        """
        # Validate enum value
        valid = {e.value for e in ActionOutcome}
        if outcome not in valid:
            raise ValueError(f"Invalid outcome '{outcome}'. Must be one of {valid}.")

        action = await self._repo.update_outcome(
            action_id=action_id,
            winery_id=winery_id,
            outcome=outcome,
            outcome_notes=outcome_notes,
        )
        if action is None:
            raise ActionNotFoundError(
                f"Action {action_id} not found for winery {winery_id}"
            )

        logger.info(
            "action_outcome_updated",
            action_id=action_id,
            outcome=outcome,
            winery_id=winery_id,
        )
        return action

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def get_action(self, action_id: int, winery_id: int) -> WinemakerAction:
        """
        Raises:
            ActionNotFoundError: if not found or winery mismatch.
        """
        action = await self._repo.get_by_id(action_id, winery_id)
        if action is None:
            raise ActionNotFoundError(
                f"Action {action_id} not found for winery {winery_id}"
            )
        return action

    async def get_actions_for_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        """Return (items, total) for a fermentation, newest-first."""
        return await self._repo.list_by_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            skip=skip,
            limit=limit,
        )

    async def get_actions_for_execution(
        self,
        execution_id: int,
        winery_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WinemakerAction], int]:
        """Return (items, total) for a protocol execution, newest-first."""
        return await self._repo.list_by_execution(
            execution_id=execution_id,
            winery_id=winery_id,
            skip=skip,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_action(self, action_id: int, winery_id: int) -> None:
        """
        Hard-delete an action.

        Raises:
            ActionNotFoundError: if not found or winery mismatch.
        """
        deleted = await self._repo.delete(action_id, winery_id)
        if not deleted:
            raise ActionNotFoundError(
                f"Action {action_id} not found for winery {winery_id}"
            )
        logger.info("action_deleted", action_id=action_id, winery_id=winery_id)
