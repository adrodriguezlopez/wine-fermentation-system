"""
Unit tests for ActionService (ADR-041).

All tests use MagicMock / AsyncMock to avoid any database dependency.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.fermentation.src.domain.entities.winemaker_action import (
    WinemakerAction,
)
from src.modules.fermentation.src.domain.enums.step_type import (
    ActionType,
    ActionOutcome,
)
from src.modules.fermentation.src.service_component.services.action_service import (
    ActionService,
    ActionNotFoundError,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_action(**kwargs) -> WinemakerAction:
    """Build a WinemakerAction with sensible defaults."""
    defaults = dict(
        id=1,
        winery_id=10,
        taken_by_user_id=99,
        action_type=ActionType.PUMP_OVER.value,
        description="Pumped over the cap",
        taken_at=datetime(2026, 3, 22, 10, 0, 0),
        fermentation_id=5,
        execution_id=None,
        step_id=None,
        alert_id=None,
        recommendation_id=None,
        outcome=ActionOutcome.PENDING.value,
        outcome_notes=None,
        outcome_recorded_at=None,
        created_at=datetime(2026, 3, 22, 10, 0, 0),
        updated_at=datetime(2026, 3, 22, 10, 0, 0),
    )
    defaults.update(kwargs)
    action = MagicMock(spec=WinemakerAction)
    for k, v in defaults.items():
        setattr(action, k, v)
    return action


def _make_service() -> tuple[ActionService, MagicMock, MagicMock]:
    """Return (service, repo_mock, alert_repo_mock)."""
    session = MagicMock()
    service = ActionService(session=session)
    repo_mock = AsyncMock()
    alert_repo_mock = AsyncMock()
    service._repo = repo_mock
    service._alert_repo = alert_repo_mock
    return service, repo_mock, alert_repo_mock


# =============================================================================
# record_action
# =============================================================================


class TestRecordAction:
    @pytest.mark.asyncio
    async def test_creates_action_with_correct_fields(self):
        service, repo, _ = _make_service()
        expected = _make_action()
        repo.create.return_value = expected

        result = await service.record_action(
            winery_id=10,
            taken_by_user_id=99,
            action_type=ActionType.PUMP_OVER.value,
            description="Pumped over the cap",
            taken_at=datetime(2026, 3, 22, 10, 0, 0),
            fermentation_id=5,
        )

        repo.create.assert_awaited_once()
        created_arg: WinemakerAction = repo.create.call_args[0][0]
        assert created_arg.winery_id == 10
        assert created_arg.taken_by_user_id == 99
        assert created_arg.action_type == ActionType.PUMP_OVER.value
        assert created_arg.outcome == ActionOutcome.PENDING.value
        assert result is expected

    @pytest.mark.asyncio
    async def test_auto_acknowledges_linked_alert(self):
        service, repo, alert_repo = _make_service()
        repo.create.return_value = _make_action(alert_id=7)

        await service.record_action(
            winery_id=10,
            taken_by_user_id=99,
            action_type=ActionType.H2S_TREATMENT.value,
            description="Added copper",
            taken_at=datetime(2026, 3, 22, 11, 0, 0),
            alert_id=7,
        )

        alert_repo.acknowledge.assert_awaited_once_with(7)

    @pytest.mark.asyncio
    async def test_no_alert_acknowledge_when_alert_id_is_none(self):
        service, repo, alert_repo = _make_service()
        repo.create.return_value = _make_action()

        await service.record_action(
            winery_id=10,
            taken_by_user_id=99,
            action_type=ActionType.CUSTOM.value,
            description="General check",
            taken_at=datetime(2026, 3, 22, 12, 0, 0),
        )

        alert_repo.acknowledge.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_all_optional_fk_fields_forwarded(self):
        service, repo, _ = _make_service()
        repo.create.return_value = _make_action(
            execution_id=3, step_id=8, alert_id=15, recommendation_id=42
        )

        await service.record_action(
            winery_id=10,
            taken_by_user_id=99,
            action_type=ActionType.NUTRIENT_ADDITION.value,
            description="Added DAP",
            taken_at=datetime(2026, 3, 22, 9, 0, 0),
            fermentation_id=5,
            execution_id=3,
            step_id=8,
            alert_id=15,
            recommendation_id=42,
        )

        created: WinemakerAction = repo.create.call_args[0][0]
        assert created.execution_id == 3
        assert created.step_id == 8
        assert created.alert_id == 15
        assert created.recommendation_id == 42


# =============================================================================
# update_outcome
# =============================================================================


class TestUpdateOutcome:
    @pytest.mark.asyncio
    async def test_updates_outcome_to_resolved(self):
        service, repo, _ = _make_service()
        updated = _make_action(outcome=ActionOutcome.RESOLVED.value)
        repo.update_outcome.return_value = updated

        result = await service.update_outcome(
            action_id=1,
            winery_id=10,
            outcome=ActionOutcome.RESOLVED.value,
            outcome_notes="Temperature stabilised",
        )

        repo.update_outcome.assert_awaited_once_with(
            action_id=1,
            winery_id=10,
            outcome="RESOLVED",
            outcome_notes="Temperature stabilised",
        )
        assert result.outcome == ActionOutcome.RESOLVED.value

    @pytest.mark.asyncio
    async def test_raises_not_found_when_repo_returns_none(self):
        service, repo, _ = _make_service()
        repo.update_outcome.return_value = None

        with pytest.raises(ActionNotFoundError):
            await service.update_outcome(
                action_id=999,
                winery_id=10,
                outcome=ActionOutcome.NO_EFFECT.value,
            )

    @pytest.mark.asyncio
    async def test_raises_value_error_on_invalid_outcome(self):
        service, repo, _ = _make_service()

        with pytest.raises(ValueError, match="Invalid outcome"):
            await service.update_outcome(
                action_id=1, winery_id=10, outcome="INVALID_STATUS"
            )

        repo.update_outcome.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "outcome",
        [
            ActionOutcome.PENDING.value,
            ActionOutcome.RESOLVED.value,
            ActionOutcome.NO_EFFECT.value,
            ActionOutcome.WORSENED.value,
        ],
    )
    async def test_all_valid_outcomes_accepted(self, outcome):
        service, repo, _ = _make_service()
        repo.update_outcome.return_value = _make_action(outcome=outcome)

        result = await service.update_outcome(
            action_id=1, winery_id=10, outcome=outcome
        )
        assert result.outcome == outcome


# =============================================================================
# get_action
# =============================================================================


class TestGetAction:
    @pytest.mark.asyncio
    async def test_returns_action_when_found(self):
        service, repo, _ = _make_service()
        action = _make_action()
        repo.get_by_id.return_value = action

        result = await service.get_action(action_id=1, winery_id=10)

        repo.get_by_id.assert_awaited_once_with(1, 10)
        assert result is action

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        service, repo, _ = _make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(ActionNotFoundError):
            await service.get_action(action_id=999, winery_id=10)


# =============================================================================
# get_actions_for_fermentation
# =============================================================================


class TestGetActionsForFermentation:
    @pytest.mark.asyncio
    async def test_returns_paginated_results(self):
        service, repo, _ = _make_service()
        actions = [_make_action(id=i) for i in range(3)]
        repo.list_by_fermentation.return_value = (actions, 3)

        items, total = await service.get_actions_for_fermentation(
            fermentation_id=5, winery_id=10, skip=0, limit=10
        )

        assert total == 3
        assert len(items) == 3
        repo.list_by_fermentation.assert_awaited_once_with(
            fermentation_id=5, winery_id=10, skip=0, limit=10
        )

    @pytest.mark.asyncio
    async def test_empty_list_when_no_actions(self):
        service, repo, _ = _make_service()
        repo.list_by_fermentation.return_value = ([], 0)

        items, total = await service.get_actions_for_fermentation(
            fermentation_id=99, winery_id=10
        )

        assert items == []
        assert total == 0


# =============================================================================
# get_actions_for_execution
# =============================================================================


class TestGetActionsForExecution:
    @pytest.mark.asyncio
    async def test_delegates_to_repository(self):
        service, repo, _ = _make_service()
        actions = [_make_action(execution_id=3)]
        repo.list_by_execution.return_value = (actions, 1)

        items, total = await service.get_actions_for_execution(
            execution_id=3, winery_id=10, skip=0, limit=50
        )

        repo.list_by_execution.assert_awaited_once_with(
            execution_id=3, winery_id=10, skip=0, limit=50
        )
        assert total == 1


# =============================================================================
# delete_action
# =============================================================================


class TestDeleteAction:
    @pytest.mark.asyncio
    async def test_succeeds_when_action_exists(self):
        service, repo, _ = _make_service()
        repo.delete.return_value = True

        await service.delete_action(action_id=1, winery_id=10)

        repo.delete.assert_awaited_once_with(1, 10)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_action_missing(self):
        service, repo, _ = _make_service()
        repo.delete.return_value = False

        with pytest.raises(ActionNotFoundError):
            await service.delete_action(action_id=999, winery_id=10)
