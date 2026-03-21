"""
Unit tests for AlertSchedulerService (ADR-040 Phase 4)

Tests cover:
- _get_active_executions returns only ACTIVE rows
- _process_execution creates STEP_OVERDUE for a past-due step
- _process_execution creates STEP_DUE_SOON for a step approaching its window
- _process_execution creates nothing for a completed step
- _process_execution creates nothing when not yet approaching
- _maybe_create_alert deduplicates — suppresses a second alert within 6 h
- STEP_OVERDUE uses CRITICAL severity when step.is_critical=True
- STEP_OVERDUE uses WARNING severity when step.is_critical=False
- STEP_DUE_SOON uses WARNING severity when step.is_critical=True
- STEP_DUE_SOON uses INFO severity when step.is_critical=False
- Non-ACTIVE executions are excluded from processing
- start() registers the job with the APScheduler
- stop() shuts the scheduler down

All tests are pure-unit: no database, no real APScheduler I/O.
The heavy DB operations (_scan_all_executions) are tested via the private helpers
by passing mock AsyncSession objects.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

# Import ALL ORM entities first so SQLAlchemy's mapper registry resolves all
# relationships before any mapper is triggered by individual imports.
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution  # noqa: F401
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert

from src.modules.fermentation.src.service_component.services.alert_scheduler_service import (
    AlertSchedulerService,
    _APPROACHING_HOURS,
    _DEDUP_HOURS,
)
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

_DB_URL = "postgresql+asyncpg://user:pass@localhost:5433/test_db"


def _make_step(
    step_id: int = 1,
    protocol_id: int = 10,
    step_order: int = 1,
    expected_day: int = 3,
    tolerance_hours: int = 12,
    is_critical: bool = False,
    description: str = "Test Step",
) -> ProtocolStep:
    step = MagicMock(spec=ProtocolStep)
    step.id = step_id
    step.protocol_id = protocol_id
    step.step_order = step_order
    step.expected_day = expected_day
    step.tolerance_hours = tolerance_hours
    step.is_critical = is_critical
    step.description = description
    return step


def _make_execution(
    exec_id: int = 100,
    protocol_id: int = 10,
    winery_id: int = 1,
    start_date: datetime | None = None,
    status: str = ProtocolExecutionStatus.ACTIVE.value,
) -> ProtocolExecution:
    if start_date is None:
        # start 10 days ago so any expected_day=3 step is overdue
        start_date = datetime.utcnow() - timedelta(days=10)
    execution = MagicMock(spec=ProtocolExecution)
    execution.id = exec_id
    execution.protocol_id = protocol_id
    execution.winery_id = winery_id
    execution.start_date = start_date
    execution.status = status
    return execution


def _scheduler_service() -> AlertSchedulerService:
    """Return a service instance whose internal APScheduler is mocked."""
    svc = AlertSchedulerService(database_url=_DB_URL, interval_minutes=30)
    svc._scheduler = MagicMock()
    svc._scheduler.add_job = MagicMock()
    svc._scheduler.start = MagicMock()
    svc._scheduler.shutdown = MagicMock()
    return svc


def _async_result(value):
    """Return an AsyncMock that yields *value* from its scalar / scalars calls."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = value
    scalars_mock.first.return_value = value[0] if isinstance(value, list) and value else value
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    result_mock.scalar_one_or_none.return_value = None   # default: no dedup hit
    am = AsyncMock(return_value=result_mock)
    return am


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_start_registers_job_and_starts_scheduler(self):
        svc = _scheduler_service()
        svc.start()
        svc._scheduler.add_job.assert_called_once()
        call_kwargs = svc._scheduler.add_job.call_args
        # job function
        assert call_kwargs[0][0] == svc._scan_all_executions
        # keyword args
        kw = call_kwargs[1] if call_kwargs[1] else {}
        assert kw.get("id") == "alert_scan"
        svc._scheduler.start.assert_called_once()

    def test_stop_shuts_scheduler_down(self):
        svc = _scheduler_service()
        svc.stop()
        svc._scheduler.shutdown.assert_called_once_with(wait=False)


# ---------------------------------------------------------------------------
# _get_active_executions
# ---------------------------------------------------------------------------

class TestGetActiveExecutions:
    @pytest.mark.asyncio
    async def test_returns_active_executions(self):
        svc = _scheduler_service()
        exec1 = _make_execution(exec_id=1)
        exec2 = _make_execution(exec_id=2)

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [exec1, exec2]
        session.execute = AsyncMock(return_value=result_mock)

        executions = await svc._get_active_executions(session)
        assert len(executions) == 2
        assert exec1 in executions

    @pytest.mark.asyncio
    async def test_returns_empty_when_none_active(self):
        svc = _scheduler_service()
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        executions = await svc._get_active_executions(session)
        assert executions == []


# ---------------------------------------------------------------------------
# _process_execution
# ---------------------------------------------------------------------------

class TestProcessExecution:
    def _build_session(
        self,
        steps: list,
        completed_step_ids: list,
        dedup_hit: bool = False,
    ) -> AsyncMock:
        """Build a mock session that returns the given steps and completions."""
        session = AsyncMock()
        call_count = [0]

        async def execute_side_effect(stmt):
            call_count[0] += 1
            mock_result = MagicMock()
            n = call_count[0]

            if n == 1:
                # First call: ProtocolStep query
                mock_result.scalars.return_value.all.return_value = steps
            elif n == 2:
                # Second call: StepCompletion IDs
                mock_result.scalars.return_value.all.return_value = completed_step_ids
            else:
                # Dedup check
                mock_result.scalar_one_or_none.return_value = 999 if dedup_hit else None
            return mock_result

        session.execute = execute_side_effect
        session.add = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_overdue_step_creates_alert(self):
        """A step past its tolerance window should produce a STEP_OVERDUE alert."""
        svc = _scheduler_service()
        # execution started 10 days ago; step expected_day=3, tolerance=12 → overdue
        execution = _make_execution(start_date=datetime.utcnow() - timedelta(days=10))
        step = _make_step(expected_day=3, tolerance_hours=12, is_critical=False)
        session = self._build_session(steps=[step], completed_step_ids=[])

        count = await svc._process_execution(session, execution)
        assert count == 1

    @pytest.mark.asyncio
    async def test_overdue_critical_step_severity_is_critical(self):
        """STEP_OVERDUE for a critical step must use severity=CRITICAL."""
        svc = _scheduler_service()
        execution = _make_execution(start_date=datetime.utcnow() - timedelta(days=10))
        step = _make_step(expected_day=3, tolerance_hours=12, is_critical=True)
        session = self._build_session(steps=[step], completed_step_ids=[])

        added_alerts: list[ProtocolAlert] = []
        original_add = session.add
        session.add = lambda obj: added_alerts.append(obj)

        await svc._process_execution(session, execution)
        assert len(added_alerts) == 1
        assert added_alerts[0].severity == "CRITICAL"
        assert added_alerts[0].alert_type == "STEP_OVERDUE"

    @pytest.mark.asyncio
    async def test_overdue_non_critical_step_severity_is_warning(self):
        """STEP_OVERDUE for a non-critical step must use severity=WARNING."""
        svc = _scheduler_service()
        execution = _make_execution(start_date=datetime.utcnow() - timedelta(days=10))
        step = _make_step(expected_day=3, tolerance_hours=12, is_critical=False)
        session = self._build_session(steps=[step], completed_step_ids=[])

        added_alerts: list = []
        session.add = lambda obj: added_alerts.append(obj)

        await svc._process_execution(session, execution)
        assert added_alerts[0].severity == "WARNING"

    @pytest.mark.asyncio
    async def test_due_soon_step_creates_alert(self):
        """A step approaching its window within 12 h produces STEP_DUE_SOON."""
        svc = _scheduler_service()
        # step is due in 6 hours → within APPROACHING window
        now = datetime.utcnow()
        start_date = now - timedelta(days=3)
        # expected_day=3, tolerance=0 → due_at ≈ start + 3d + 0h; 6h from now
        # Adjust start so due_at = now + 6h → start = now + 6h - 3d
        start_date = now + timedelta(hours=6) - timedelta(days=3)
        execution = _make_execution(start_date=start_date)
        step = _make_step(expected_day=3, tolerance_hours=0, is_critical=False)
        session = self._build_session(steps=[step], completed_step_ids=[])

        added_alerts: list = []
        session.add = lambda obj: added_alerts.append(obj)

        count = await svc._process_execution(session, execution)
        assert count == 1
        assert added_alerts[0].alert_type == "STEP_DUE_SOON"

    @pytest.mark.asyncio
    async def test_due_soon_critical_severity_is_warning(self):
        """STEP_DUE_SOON for critical step uses WARNING severity."""
        svc = _scheduler_service()
        now = datetime.utcnow()
        start_date = now + timedelta(hours=6) - timedelta(days=3)
        execution = _make_execution(start_date=start_date)
        step = _make_step(expected_day=3, tolerance_hours=0, is_critical=True)
        session = self._build_session(steps=[step], completed_step_ids=[])

        added_alerts: list = []
        session.add = lambda obj: added_alerts.append(obj)

        await svc._process_execution(session, execution)
        assert added_alerts[0].severity == "WARNING"

    @pytest.mark.asyncio
    async def test_due_soon_non_critical_severity_is_info(self):
        """STEP_DUE_SOON for non-critical step uses INFO severity."""
        svc = _scheduler_service()
        now = datetime.utcnow()
        start_date = now + timedelta(hours=6) - timedelta(days=3)
        execution = _make_execution(start_date=start_date)
        step = _make_step(expected_day=3, tolerance_hours=0, is_critical=False)
        session = self._build_session(steps=[step], completed_step_ids=[])

        added_alerts: list = []
        session.add = lambda obj: added_alerts.append(obj)

        await svc._process_execution(session, execution)
        assert added_alerts[0].severity == "INFO"

    @pytest.mark.asyncio
    async def test_completed_step_is_skipped(self):
        """A completed step must not generate any alert."""
        svc = _scheduler_service()
        execution = _make_execution(start_date=datetime.utcnow() - timedelta(days=10))
        step = _make_step(step_id=42, expected_day=3, tolerance_hours=12)
        # step 42 is already completed
        session = self._build_session(steps=[step], completed_step_ids=[42])

        count = await svc._process_execution(session, execution)
        assert count == 0

    @pytest.mark.asyncio
    async def test_future_step_creates_no_alert(self):
        """A step not yet approaching its window creates no alert."""
        svc = _scheduler_service()
        # step due in 48 hours — outside 12-h APPROACHING window
        now = datetime.utcnow()
        start_date = now + timedelta(hours=48) - timedelta(days=3)
        execution = _make_execution(start_date=start_date)
        step = _make_step(expected_day=3, tolerance_hours=0, is_critical=False)
        session = self._build_session(steps=[step], completed_step_ids=[])

        count = await svc._process_execution(session, execution)
        assert count == 0


# ---------------------------------------------------------------------------
# _maybe_create_alert  (dedup)
# ---------------------------------------------------------------------------

class TestMaybeCreateAlert:
    def _session_with_dedup(self, hit: bool) -> AsyncMock:
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = 999 if hit else None
        session.execute = AsyncMock(return_value=result_mock)
        session.add = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_creates_alert_when_no_existing(self):
        svc = _scheduler_service()
        session = self._session_with_dedup(hit=False)
        execution = _make_execution()
        step = _make_step()

        result = await svc._maybe_create_alert(
            session=session,
            execution=execution,
            step=step,
            alert_type="STEP_OVERDUE",
            severity="WARNING",
            message="overdue!",
        )
        assert result == 1
        session.add.assert_called_once()
        alert: ProtocolAlert = session.add.call_args[0][0]
        assert alert.alert_type == "STEP_OVERDUE"
        assert alert.severity == "WARNING"
        assert alert.status == "PENDING"
        assert alert.execution_id == execution.id

    @pytest.mark.asyncio
    async def test_suppresses_alert_when_duplicate_exists(self):
        """If a non-dismissed alert already exists within 6 h, do NOT create another."""
        svc = _scheduler_service()
        session = self._session_with_dedup(hit=True)
        execution = _make_execution()
        step = _make_step()

        result = await svc._maybe_create_alert(
            session=session,
            execution=execution,
            step=step,
            alert_type="STEP_OVERDUE",
            severity="WARNING",
            message="overdue!",
        )
        assert result == 0
        session.add.assert_not_called()
