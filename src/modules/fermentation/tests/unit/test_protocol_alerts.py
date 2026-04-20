"""
Tests for ADR-040: ProtocolAlert entity, ProtocolAlertRepository, and
ProtocolAlertService persistence integration.

Following the pattern of test_protocol_repositories.py (contract + entity tests)
and the fermentation unit test conventions.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.domain.repositories.protocol_alert_repository_interface import (
    IProtocolAlertRepository,
)
from src.modules.fermentation.src.service_component.services.protocol_alert_service import (
    AlertDetail,
    AlertStatus,
    AlertType,
    ProtocolAlertService,
)

# =============================================================================
# Helpers
# =============================================================================


def make_alert(
    *,
    id: int = 1,
    execution_id: int = 10,
    protocol_id: int = 1,
    winery_id: int = 5,
    step_id: Optional[int] = 2,
    step_name: Optional[str] = "H2S Check",
    alert_type: str = "STEP_OVERDUE",
    severity: str = "WARNING",
    status: str = "PENDING",
    message: str = "Step is overdue",
) -> ProtocolAlert:
    """Create a ProtocolAlert ORM object for testing (without DB).

    Uses the regular SQLAlchemy constructor (which sets up _sa_instance_state so
    entity methods like acknowledge()/dismiss() work), then writes DB-managed
    fields (id, created_at, timestamps) directly into __dict__ to bypass the
    descriptor protocol without triggering a database flush.
    """
    alert = ProtocolAlert(
        execution_id=execution_id,
        protocol_id=protocol_id,
        winery_id=winery_id,
        step_id=step_id,
        step_name=step_name,
        alert_type=alert_type,
        severity=severity,
        status=status,
        message=message,
    )
    # Write DB-managed / auto-generated fields directly into __dict__ so they
    # are visible to attribute reads without going through the descriptor set path.
    alert.__dict__["id"] = id
    alert.__dict__.setdefault("created_at", datetime(2026, 3, 1, 10, 0, 0))
    alert.__dict__.setdefault("sent_at", None)
    alert.__dict__.setdefault("acknowledged_at", None)
    alert.__dict__.setdefault("dismissed_at", None)
    return alert


# =============================================================================
# ProtocolAlert entity tests
# =============================================================================


class TestProtocolAlertEntity:
    """Unit tests for the ProtocolAlert ORM entity."""

    def test_tablename(self):
        assert ProtocolAlert.__tablename__ == "protocol_alerts"

    def test_acknowledge_sets_status_and_timestamp(self):
        alert = make_alert(status="PENDING")
        before = datetime.utcnow()
        alert.acknowledge()
        after = datetime.utcnow()

        assert alert.status == "ACKNOWLEDGED"
        assert alert.acknowledged_at is not None
        assert before <= alert.acknowledged_at <= after

    def test_dismiss_sets_status_and_timestamp(self):
        alert = make_alert(status="PENDING")
        before = datetime.utcnow()
        alert.dismiss()
        after = datetime.utcnow()

        assert alert.status == "DISMISSED"
        assert alert.dismissed_at is not None
        assert before <= alert.dismissed_at <= after

    def test_mark_sent(self):
        alert = make_alert(status="PENDING")
        alert.mark_sent()
        assert alert.status == "SENT"
        assert alert.sent_at is not None

    def test_is_pending_true_when_pending(self):
        assert make_alert(status="PENDING").is_pending is True

    def test_is_pending_false_when_acknowledged(self):
        assert make_alert(status="ACKNOWLEDGED").is_pending is False

    def test_is_critical_true_for_critical_severity(self):
        assert make_alert(severity="CRITICAL").is_critical is True

    def test_is_critical_false_for_warning(self):
        assert make_alert(severity="WARNING").is_critical is False

    def test_to_dict_contains_expected_keys(self):
        alert = make_alert()
        d = alert.to_dict()
        for key in (
            "id",
            "execution_id",
            "protocol_id",
            "winery_id",
            "step_id",
            "step_name",
            "alert_type",
            "severity",
            "status",
            "message",
            "created_at",
            "sent_at",
            "acknowledged_at",
            "dismissed_at",
        ):
            assert key in d

    def test_to_dict_timestamps_are_isoformat(self):
        alert = make_alert()
        alert.acknowledged_at = datetime(2026, 3, 2, 12, 0, 0)
        d = alert.to_dict()
        assert d["acknowledged_at"] == "2026-03-02T12:00:00"
        assert d["sent_at"] is None

    def test_repr(self):
        alert = make_alert(
            id=7,
            execution_id=3,
            alert_type="CRITICAL_DEVIATION",
            severity="CRITICAL",
            status="PENDING",
        )
        r = repr(alert)
        assert "7" in r
        assert "CRITICAL_DEVIATION" in r


# =============================================================================
# IProtocolAlertRepository interface contract
# =============================================================================


class TestIProtocolAlertRepositoryContract:
    """Verify the interface declares all required abstract methods."""

    def test_interface_is_abstract(self):
        import inspect

        assert inspect.isabstract(IProtocolAlertRepository)

    def test_required_methods_exist(self):
        required = {
            "create",
            "create_many",
            "get_by_id",
            "get_by_execution",
            "get_pending_by_winery",
            "acknowledge",
            "dismiss",
            "count_pending",
        }
        actual = set(IProtocolAlertRepository.__abstractmethods__)
        assert required == actual


# =============================================================================
# ProtocolAlertRepository unit tests (mocked session)
# =============================================================================


class TestProtocolAlertRepository:
    """Unit tests for the concrete ProtocolAlertRepository."""

    def _make_repo(self):
        from src.modules.fermentation.src.repository_component.protocol_alert_repository import (
            ProtocolAlertRepository,
        )

        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()
        repo = ProtocolAlertRepository(session=session)
        return repo, session

    @pytest.mark.asyncio
    async def test_create_adds_and_flushes(self):
        repo, session = self._make_repo()
        alert = make_alert()
        result = await repo.create(alert)
        session.add.assert_called_once_with(alert)
        session.flush.assert_awaited_once()
        assert result is alert

    @pytest.mark.asyncio
    async def test_create_many_returns_empty_for_empty_input(self):
        repo, session = self._make_repo()
        result = await repo.create_many([])
        assert result == []
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_many_adds_all_and_flushes_once(self):
        repo, session = self._make_repo()
        alerts = [make_alert(id=i) for i in range(3)]
        result = await repo.create_many(alerts)
        assert session.add.call_count == 3
        session.flush.assert_awaited_once()
        assert result == alerts

    @pytest.mark.asyncio
    async def test_get_by_id_returns_alert(self):
        repo, session = self._make_repo()
        alert = make_alert(id=42)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = alert
        session.execute.return_value = mock_result
        result = await repo.get_by_id(42)
        assert result is alert

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        repo, session = self._make_repo()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result
        result = await repo.get_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_execution_returns_list(self):
        repo, session = self._make_repo()
        alerts = [make_alert(id=i) for i in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = alerts
        session.execute.return_value = mock_result
        result = await repo.get_by_execution(execution_id=10)
        assert result == alerts

    @pytest.mark.asyncio
    async def test_get_by_execution_empty(self):
        repo, session = self._make_repo()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result
        result = await repo.get_by_execution(execution_id=99)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_pending_by_winery_returns_list(self):
        repo, session = self._make_repo()
        alerts = [make_alert(winery_id=5)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = alerts
        session.execute.return_value = mock_result
        result = await repo.get_pending_by_winery(winery_id=5)
        assert result == alerts

    @pytest.mark.asyncio
    async def test_acknowledge_returns_updated_alert(self):
        repo, session = self._make_repo()
        alert = make_alert(status="PENDING")

        # get_by_id returns the alert
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = alert
        session.execute.return_value = mock_result

        result = await repo.acknowledge(alert.id)
        assert result is alert
        assert result.status == "ACKNOWLEDGED"
        assert result.acknowledged_at is not None
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_acknowledge_returns_none_when_not_found(self):
        repo, session = self._make_repo()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result
        result = await repo.acknowledge(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_dismiss_returns_updated_alert(self):
        repo, session = self._make_repo()
        alert = make_alert(status="PENDING")
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = alert
        session.execute.return_value = mock_result

        result = await repo.dismiss(alert.id)
        assert result is alert
        assert result.status == "DISMISSED"

    @pytest.mark.asyncio
    async def test_count_pending_returns_int(self):
        repo, session = self._make_repo()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        session.execute.return_value = mock_result
        count = await repo.count_pending(execution_id=10)
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_pending_zero(self):
        repo, session = self._make_repo()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        session.execute.return_value = mock_result
        count = await repo.count_pending(execution_id=10)
        assert count == 0


# =============================================================================
# ProtocolAlertService — repository integration tests
# =============================================================================


class TestProtocolAlertServiceWithRepo:
    """
    Test that ProtocolAlertService correctly persists alerts via
    the alert_repo when it is wired in.
    """

    def _make_service(self, alert_repo=None):
        """Build a ProtocolAlertService with mocked dependencies."""
        from src.modules.fermentation.src.domain.entities.protocol_execution import (
            ProtocolExecution,
        )
        from src.modules.fermentation.src.domain.entities.protocol_protocol import (
            FermentationProtocol,
        )
        from src.modules.fermentation.src.domain.entities.protocol_step import (
            ProtocolStep,
        )

        # Minimal mock execution
        execution = MagicMock(spec=ProtocolExecution)
        execution.id = 10
        execution.winery_id = 5
        execution.protocol_id = 1
        execution.start_date = datetime.utcnow() - timedelta(days=10)
        execution.status = "ACTIVE"
        execution.compliance_score = 70.0

        # Minimal mock protocol
        protocol = MagicMock(spec=FermentationProtocol)
        protocol.id = 1
        protocol.expected_duration_days = 14

        # Minimal mock step
        step = MagicMock(spec=ProtocolStep)
        step.id = 2
        step.description = "H2S Check"
        step.expected_day = 3
        step.tolerance_hours = 6
        step.is_critical = True

        execution_repo = MagicMock()
        execution_repo.get_by_id = AsyncMock(return_value=execution)

        protocol_repo = MagicMock()
        protocol_repo.get_by_id = AsyncMock(return_value=protocol)

        step_repo = MagicMock()

        compliance_service = MagicMock()
        # Return one overdue step
        overdue_step = MagicMock()
        overdue_step.id = step.id
        overdue_step.description = step.description
        overdue_step.expected_day = step.expected_day
        overdue_step.tolerance_hours = step.tolerance_hours
        compliance_service.get_overdue_steps = AsyncMock(return_value=[overdue_step])
        compliance_service.detect_deviations = AsyncMock(return_value=[])

        svc = ProtocolAlertService(
            protocol_repository=protocol_repo,
            execution_repository=execution_repo,
            step_repository=step_repo,
            compliance_service=compliance_service,
            alert_repository=alert_repo,
        )
        return svc, execution

    @pytest.mark.asyncio
    async def test_service_accepts_none_alert_repo(self):
        """Service initializes without an alert_repo (backward compatible)."""
        svc, _ = self._make_service(alert_repo=None)
        assert svc.alert_repo is None

    @pytest.mark.asyncio
    async def test_send_overdue_alert_calls_create_many_when_repo_wired(self):
        alert_repo = MagicMock(spec=IProtocolAlertRepository)
        alert_repo.create_many = AsyncMock(return_value=[])
        svc, _ = self._make_service(alert_repo=alert_repo)

        result = await svc.send_overdue_alert(execution_id=10, winery_id=5)

        # Should have generated at least one alert
        assert len(result) >= 1
        alert_repo.create_many.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_overdue_alert_no_repo_does_not_crash(self):
        svc, _ = self._make_service(alert_repo=None)
        result = await svc.send_overdue_alert(execution_id=10, winery_id=5)
        # Returns in-memory AlertDetail list even without repo
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_pending_alerts_uses_repo_when_wired(self):
        alert_repo = MagicMock(spec=IProtocolAlertRepository)
        orm_alert = make_alert(execution_id=10, winery_id=5, status="PENDING")
        alert_repo.get_by_execution = AsyncMock(return_value=[orm_alert])
        svc, _ = self._make_service(alert_repo=alert_repo)

        result = await svc.get_pending_alerts(execution_id=10, winery_id=5)
        assert len(result) == 1
        assert isinstance(result[0], AlertDetail)
        assert result[0].alert_id == orm_alert.id
        alert_repo.get_by_execution.assert_awaited_once_with(
            execution_id=10,
            status="PENDING",
            alert_type=None,
        )

    @pytest.mark.asyncio
    async def test_get_pending_alerts_returns_empty_without_repo(self):
        svc, _ = self._make_service(alert_repo=None)
        result = await svc.get_pending_alerts(execution_id=10, winery_id=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_acknowledge_alert_raises_without_repo(self):
        svc, _ = self._make_service(alert_repo=None)
        with pytest.raises(ValueError, match="repository not configured"):
            await svc.acknowledge_alert(execution_id=10, alert_id=1, winery_id=5)

    @pytest.mark.asyncio
    async def test_acknowledge_alert_raises_when_not_found(self):
        alert_repo = MagicMock(spec=IProtocolAlertRepository)
        alert_repo.acknowledge = AsyncMock(return_value=None)
        svc, _ = self._make_service(alert_repo=alert_repo)

        with pytest.raises(ValueError, match="not found"):
            await svc.acknowledge_alert(execution_id=10, alert_id=999, winery_id=5)

    @pytest.mark.asyncio
    async def test_acknowledge_alert_returns_alert_detail(self):
        alert_repo = MagicMock(spec=IProtocolAlertRepository)
        orm_alert = make_alert(id=42, status="ACKNOWLEDGED")
        orm_alert.acknowledged_at = datetime.utcnow()
        alert_repo.acknowledge = AsyncMock(return_value=orm_alert)
        svc, _ = self._make_service(alert_repo=alert_repo)

        result = await svc.acknowledge_alert(execution_id=10, alert_id=42, winery_id=5)
        assert isinstance(result, AlertDetail)
        assert result.alert_id == 42
        assert result.status == AlertStatus.ACKNOWLEDGED
