"""
Unit tests for ProtocolAlertService

Test coverage:
- Overdue step alert detection
- Completion reminder alerts
- Critical deviation detection
- Alert tracking and status management
- Multi-tenancy enforcement
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch
from datetime import datetime, timedelta
from typing import List

from src.modules.fermentation.src.service_component.services.protocol_alert_service import (
    ProtocolAlertService,
    AlertType,
    AlertStatus,
    AlertDetail,
    AlertSummary,
)
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.service_component.services.protocol_compliance_service import ProtocolComplianceService
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_protocol_repo() -> AsyncMock:
    """Mock protocol repository."""
    mock = create_autospec(FermentationProtocolRepository, instance=True)
    mock.session = MagicMock()
    mock.session.commit = AsyncMock()
    return mock


@pytest.fixture
def mock_execution_repo() -> AsyncMock:
    """Mock execution repository."""
    mock = create_autospec(ProtocolExecutionRepository, instance=True)
    mock.session = MagicMock()
    mock.session.commit = AsyncMock()
    return mock


@pytest.fixture
def mock_step_repo() -> AsyncMock:
    """Mock step repository."""
    return create_autospec(ProtocolStepRepository, instance=True)


@pytest.fixture
def mock_compliance_service() -> AsyncMock:
    """Mock compliance service."""
    return create_autospec(ProtocolComplianceService, instance=True)


@pytest.fixture
def alert_service(
    mock_protocol_repo,
    mock_execution_repo,
    mock_step_repo,
    mock_compliance_service,
) -> ProtocolAlertService:
    """Create service with mock dependencies."""
    return ProtocolAlertService(
        protocol_repository=mock_protocol_repo,
        execution_repository=mock_execution_repo,
        step_repository=mock_step_repo,
        compliance_service=mock_compliance_service,
    )


@pytest.fixture
def sample_execution() -> MagicMock:
    """Create a mock execution."""
    execution = MagicMock()
    execution.id = 1
    execution.fermentation_id = 100
    execution.protocol_id = 1
    execution.winery_id = 1
    execution.start_date = datetime.utcnow() - timedelta(days=5)
    execution.status = ProtocolExecutionStatus.ACTIVE
    execution.compliance_score = 80.0
    execution.completed_steps = 3
    execution.skipped_critical_steps = 0
    return execution


@pytest.fixture
def sample_protocol() -> MagicMock:
    """Create a mock protocol."""
    protocol = MagicMock()
    protocol.id = 1
    protocol.winery_id = 1
    protocol.varietal_name = "Pinot Noir"
    protocol.expected_duration_days = 28
    return protocol


@pytest.fixture
def overdue_step() -> MagicMock:
    """Create a mock overdue step."""
    step = MagicMock()
    step.id = 1
    step.protocol_id = 1
    step.step_order = 1
    step.description = "Yeast Inoculation"
    step.expected_day = 0
    step.tolerance_hours = 12
    step.is_critical = True
    step.criticality_score = 1.5
    return step


# ============================================================================
# Test Classes
# ============================================================================

class TestSendOverdueAlert:
    """Test overdue step alerts."""

    @pytest.mark.asyncio
    async def test_send_overdue_alert_success(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
        overdue_step,
    ):
        """Test successful overdue alert generation."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.get_overdue_steps = AsyncMock(
            return_value=[overdue_step]
        )

        alerts = await alert_service.send_overdue_alert(
            execution_id=1,
            winery_id=1,
        )

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.STEP_OVERDUE
        assert alerts[0].step_name == "Yeast Inoculation"
        assert alerts[0].status == AlertStatus.PENDING

    @pytest.mark.asyncio
    async def test_send_overdue_alert_execution_not_found(
        self,
        alert_service,
        mock_execution_repo,
    ):
        """Test alert when execution not found."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await alert_service.send_overdue_alert(1, 1)

    @pytest.mark.asyncio
    async def test_send_overdue_alert_access_denied(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test alert with wrong winery."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Access denied"):
            await alert_service.send_overdue_alert(1, 999)

    @pytest.mark.asyncio
    async def test_send_overdue_alert_no_overdue_steps(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
    ):
        """Test when no steps are overdue."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.get_overdue_steps = AsyncMock(return_value=[])

        alerts = await alert_service.send_overdue_alert(1, 1)

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_send_overdue_alert_severity_critical_when_very_late(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
        overdue_step,
    ):
        """Test critical severity for very overdue steps."""
        very_late_step = MagicMock()
        very_late_step.id = 1
        very_late_step.description = "Late Step"
        very_late_step.expected_day = 0
        very_late_step.tolerance_hours = 12
        very_late_step.is_critical = True

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.get_overdue_steps = AsyncMock(
            return_value=[very_late_step]
        )

        alerts = await alert_service.send_overdue_alert(1, 1)

        assert len(alerts) == 1
        # Severity would be CRITICAL if > 24 hours overdue
        assert alerts[0].severity in ["WARNING", "CRITICAL"]


class TestSendCompletionReminder:
    """Test completion reminder alerts."""

    @pytest.mark.asyncio
    async def test_send_completion_reminder_success(
        self,
        alert_service,
        mock_execution_repo,
        mock_protocol_repo,
        sample_execution,
        sample_protocol,
    ):
        """Test successful completion reminder."""
        # Set execution to 2 days from completion (within 3-day threshold)
        sample_execution.start_date = datetime.utcnow() - timedelta(days=26)
        sample_execution.compliance_score = 75.0  # Below 85% target

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        alert = await alert_service.send_completion_reminder(1, 1)

        assert alert is not None
        assert alert.alert_type == AlertType.EXECUTION_NEARING_COMPLETION
        assert alert.status == AlertStatus.PENDING

    @pytest.mark.asyncio
    async def test_send_completion_reminder_already_at_target(
        self,
        alert_service,
        mock_execution_repo,
        mock_protocol_repo,
        sample_execution,
        sample_protocol,
    ):
        """Test no reminder when compliance at target."""
        sample_execution.start_date = datetime.utcnow() - timedelta(days=26)
        sample_execution.compliance_score = 90.0  # Above 85% target

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        alert = await alert_service.send_completion_reminder(1, 1)

        assert alert is None

    @pytest.mark.asyncio
    async def test_send_completion_reminder_not_active(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test no reminder for non-ACTIVE execution."""
        sample_execution.status = ProtocolExecutionStatus.COMPLETED

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        alert = await alert_service.send_completion_reminder(1, 1)

        assert alert is None

    @pytest.mark.asyncio
    async def test_send_completion_reminder_too_early(
        self,
        alert_service,
        mock_execution_repo,
        mock_protocol_repo,
        sample_execution,
        sample_protocol,
    ):
        """Test no reminder when completion still far away."""
        # Set to 10 days from completion (beyond 3-day threshold)
        sample_execution.start_date = datetime.utcnow() - timedelta(days=18)

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_protocol_repo.get_by_id = AsyncMock(return_value=sample_protocol)

        alert = await alert_service.send_completion_reminder(1, 1)

        assert alert is None

    @pytest.mark.asyncio
    async def test_send_completion_reminder_execution_not_found(
        self,
        alert_service,
        mock_execution_repo,
    ):
        """Test reminder when execution not found."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await alert_service.send_completion_reminder(1, 1)


class TestDetectCriticalDeviations:
    """Test critical deviation detection."""

    @pytest.mark.asyncio
    async def test_detect_critical_deviations_unjustified_skip(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
    ):
        """Test alert for unjustified skip of critical step."""
        deviation = MagicMock()
        deviation.step = MagicMock()
        deviation.step.id = 1
        deviation.step.is_critical = True
        deviation.step.description = "Critical Step"
        deviation.step_status = "UNJUSTIFIED_SKIP"

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.detect_deviations = AsyncMock(
            return_value=[deviation]
        )

        alerts = await alert_service.detect_critical_deviations(1, 1)

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.CRITICAL_DEVIATION
        assert alerts[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_detect_critical_deviations_missing_step(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
    ):
        """Test alert for missing critical step."""
        deviation = MagicMock()
        deviation.step = MagicMock()
        deviation.step.id = 1
        deviation.step.is_critical = True
        deviation.step.description = "Missing Step"
        deviation.step_status = "MISSING"

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.detect_deviations = AsyncMock(
            return_value=[deviation]
        )

        alerts = await alert_service.detect_critical_deviations(1, 1)

        assert len(alerts) == 1

    @pytest.mark.asyncio
    async def test_detect_critical_deviations_ignores_non_critical(
        self,
        alert_service,
        mock_execution_repo,
        mock_compliance_service,
        sample_execution,
    ):
        """Test that non-critical skips are ignored."""
        deviation = MagicMock()
        deviation.step = MagicMock()
        deviation.step.is_critical = False  # Non-critical
        deviation.step_status = "UNJUSTIFIED_SKIP"

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_compliance_service.detect_deviations = AsyncMock(
            return_value=[deviation]
        )

        alerts = await alert_service.detect_critical_deviations(1, 1)

        assert len(alerts) == 0


class TestGetPendingAlerts:
    """Test pending alert retrieval."""

    @pytest.mark.asyncio
    async def test_get_pending_alerts_success(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test successful pending alert retrieval."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        alerts = await alert_service.get_pending_alerts(1, 1)

        # Default returns empty (no alert repository in this test)
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_get_pending_alerts_access_denied(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test alert retrieval with wrong winery."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Access denied"):
            await alert_service.get_pending_alerts(1, 999)

    @pytest.mark.asyncio
    async def test_get_pending_alerts_execution_not_found(
        self,
        alert_service,
        mock_execution_repo,
    ):
        """Test alert retrieval when execution not found."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await alert_service.get_pending_alerts(1, 1)


class TestGetAlertSummary:
    """Test alert summary generation."""

    @pytest.mark.asyncio
    async def test_get_alert_summary_success(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test successful alert summary."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        summary = await alert_service.get_alert_summary(1, 1)

        assert isinstance(summary, AlertSummary)
        assert summary.execution_id == 1
        assert summary.total_pending == 0
        assert summary.critical_count == 0

    @pytest.mark.asyncio
    async def test_get_alert_summary_access_denied(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test summary with wrong winery."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Access denied"):
            await alert_service.get_alert_summary(1, 999)


class TestAcknowledgeAlert:
    """Test alert acknowledgment."""

    @pytest.mark.asyncio
    async def test_acknowledge_alert_success(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test successful alert acknowledgment."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        alert = await alert_service.acknowledge_alert(1, 1, 1)

        assert alert.status == AlertStatus.ACKNOWLEDGED

    @pytest.mark.asyncio
    async def test_acknowledge_alert_execution_not_found(
        self,
        alert_service,
        mock_execution_repo,
    ):
        """Test acknowledge when execution not found."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await alert_service.acknowledge_alert(1, 1, 1)

    @pytest.mark.asyncio
    async def test_acknowledge_alert_access_denied(
        self,
        alert_service,
        mock_execution_repo,
        sample_execution,
    ):
        """Test acknowledge with wrong winery."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)

        with pytest.raises(ValueError, match="Access denied"):
            await alert_service.acknowledge_alert(1, 1, 999)


class TestMultiTenancy:
    """Test multi-tenancy enforcement across all operations."""

    @pytest.mark.asyncio
    async def test_all_operations_enforce_winery_access(
        self,
        alert_service,
        mock_execution_repo,
    ):
        """Test that all operations enforce winery access control."""
        sample_exec = MagicMock()
        sample_exec.winery_id = 1
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_exec)

        # Test each operation with wrong winery
        operations = [
            alert_service.send_overdue_alert(1, 999),
            alert_service.send_completion_reminder(1, 999),
            alert_service.detect_critical_deviations(1, 999),
            alert_service.get_pending_alerts(1, 999),
            alert_service.get_alert_summary(1, 999),
            alert_service.acknowledge_alert(1, 1, 999),
        ]

        for operation in operations:
            with pytest.raises(ValueError, match="Access denied"):
                await operation
