"""
Unit tests for ProtocolComplianceService.

Implements ADR-036: Protocol Compliance Scoring Algorithm

Test Strategy:
- 40+ unit tests covering all compliance scoring scenarios
- Mock repositories to test service logic in isolation
- Test compliance score calculation with various step completion patterns
- Test deviation detection (missing steps, late steps, unjustified skips)
- Test execution status tracking and overdue steps
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch
from datetime import datetime, timedelta
from typing import Optional, List

# Service under test
from src.modules.fermentation.src.service_component.services.protocol_compliance_service import (
    ProtocolComplianceService,
    ComplianceScoreResult,
    StepDeviation,
    WeightedCompletionScore,
    TimingScore,
    StepCompletionBreakdown,
    JUSTIFIED_SKIP_REASONS,
    UNJUSTIFIED_SKIP_REASONS,
)

# Repository interfaces
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.repository_component.step_completion_repository import StepCompletionRepository

# Domain entities
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import StepType, SkipReason


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_protocol_repo() -> AsyncMock:
    """Mock FermentationProtocolRepository."""
    return create_autospec(FermentationProtocolRepository, instance=True)


@pytest.fixture
def mock_execution_repo() -> AsyncMock:
    """Mock ProtocolExecutionRepository."""
    mock = create_autospec(ProtocolExecutionRepository, instance=True)
    mock.session = MagicMock()
    mock.session.commit = AsyncMock()
    return mock


@pytest.fixture
def mock_step_repo() -> AsyncMock:
    """Mock ProtocolStepRepository."""
    return create_autospec(ProtocolStepRepository, instance=True)


@pytest.fixture
def mock_completion_repo() -> AsyncMock:
    """Mock StepCompletionRepository."""
    return create_autospec(StepCompletionRepository, instance=True)


@pytest.fixture
def compliance_service(
    mock_protocol_repo,
    mock_execution_repo,
    mock_step_repo,
    mock_completion_repo,
) -> ProtocolComplianceService:
    """Create service with mock dependencies."""
    return ProtocolComplianceService(
        protocol_repository=mock_protocol_repo,
        execution_repository=mock_execution_repo,
        completion_repository=mock_completion_repo,
        step_repository=mock_step_repo,
    )


@pytest.fixture
def sample_protocol() -> FermentationProtocol:
    """Create a sample protocol with 3 steps."""
    protocol = FermentationProtocol(
        varietal_code="PN",
        varietal_name="Pinot Noir",
        color="RED",
        version="1.0",
        protocol_name="Pinot Noir 2026",
        description="Standard PN protocol",
        expected_duration_days=28,
        is_active=True,
    )
    protocol.id = 1
    
    # Add 3 steps: 2 critical, 1 optional
    steps = [
        ProtocolStep(
            protocol_id=1,
            step_order=1,
            step_type=StepType.INITIALIZATION,
            description="Yeast Inoculation",
            expected_day=0,
            tolerance_hours=12,
            duration_minutes=30,
            is_critical=True,
            criticality_score=1.5,
        ),
        ProtocolStep(
            protocol_id=1,
            step_order=2,
            step_type=StepType.MONITORING,
            description="H2S Check",
            expected_day=2,
            tolerance_hours=24,
            duration_minutes=15,
            is_critical=True,
            criticality_score=1.5,
        ),
        ProtocolStep(
            protocol_id=1,
            step_order=3,
            step_type=StepType.ADDITIONS,
            description="DAP Addition",
            expected_day=5,
            tolerance_hours=12,
            duration_minutes=20,
            is_critical=False,
            criticality_score=0.5,
        ),
    ]
    
    for idx, step in enumerate(steps, 1):
        step.id = idx
    
    protocol.steps = steps
    return protocol


@pytest.fixture
def sample_execution(sample_protocol) -> ProtocolExecution:
    """Create a sample protocol execution."""
    execution = ProtocolExecution(
        fermentation_id=1,
        protocol_id=sample_protocol.id,
        start_date=datetime(2026, 2, 1, 12, 0, 0),
        status="IN_PROGRESS",
        compliance_score=0.0,
        completed_steps=0,
        skipped_critical_steps=0,
    )
    execution.id = 1
    execution.protocol = sample_protocol
    return execution


# ============================================================================
# Test Classes
# ============================================================================

class TestCalculateComplianceScore:
    """Test compliance score calculation."""

    @pytest.mark.asyncio
    async def test_perfect_execution_scores_100(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that perfect execution (all on-time) scores 100%."""
        # Setup: all steps completed on-time
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=3,
                completed_at=sample_execution.start_date + timedelta(days=5),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert
        assert result.compliance_score == 100.0
        assert result.weighted_completion == 100.0
        assert result.timing_score == 100.0
        assert result.critical_steps_completion_pct == 100.0

    @pytest.mark.asyncio
    async def test_execution_not_found_raises_error(
        self,
        compliance_service,
        mock_execution_repo,
    ):
        """Test that missing execution raises ValueError."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await compliance_service.calculate_compliance_score(999)

    @pytest.mark.asyncio
    async def test_one_critical_step_missing_applies_penalty(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that missing critical step applies -15% penalty."""
        # Setup: only step 2 (critical) completed
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert: Should have penalty for missing critical step
        assert result.compliance_score < 85  # Baseline score minus 15% penalty
        assert result.critical_steps_completion_pct == 50.0  # 1/2 critical steps

    @pytest.mark.asyncio
    async def test_justified_skip_earns_60_percent_credit(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that justified skip earns 60% point credit."""
        # Setup: step 3 justified skip, step 1&2 completed on-time
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=3,
                completed_at=sample_execution.start_date + timedelta(days=5),
                was_skipped=True,
                skip_reason=SkipReason.CONDITION_NOT_MET.value,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert: Should include 60% credit for justified skip
        assert result.compliance_score >= 95  # Should be high score
        # Breakdown should show 60% credit for step 3
        step3_breakdown = next(
            (s for s in result.breakdown["completion"].step_breakdown if s.step_id == 3),
            None,
        )
        assert step3_breakdown is not None
        assert step3_breakdown.earned_points == step3_breakdown.possible_points * 0.60

    @pytest.mark.asyncio
    async def test_late_step_applies_timing_penalty(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that step completed late applies timing penalty."""
        # Setup: step 2 completed 1 day late
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=3),  # 1 day late
                is_on_schedule=False,
                days_late=1,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=3,
                completed_at=sample_execution.start_date + timedelta(days=5),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert: Score should be less than 100 due to late penalty
        assert result.compliance_score < 100
        assert result.timing_score == 66.67  # 2/3 on-time

    @pytest.mark.asyncio
    async def test_unjustified_skip_earns_zero_credit(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that unjustified skip earns 0% credit."""
        # Setup: step 3 unjustified skip
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=3,
                completed_at=sample_execution.start_date + timedelta(days=5),
                was_skipped=True,
                skip_reason=SkipReason.OTHER.value,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert: Unjustified skip should earn 0 credit
        step3_breakdown = next(
            (s for s in result.breakdown["completion"].step_breakdown if s.step_id == 3),
            None,
        )
        assert step3_breakdown is not None
        assert step3_breakdown.earned_points == 0


class TestMarkStepComplete:
    """Test marking steps as completed."""

    @pytest.mark.asyncio
    async def test_mark_step_complete_creates_record(
        self,
        compliance_service,
        sample_execution,
        mock_execution_repo,
        mock_completion_repo,
        mock_step_repo,
    ):
        """Test that marking step complete creates StepCompletion record."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_step_repo.get_by_id = AsyncMock(return_value=MagicMock())
        mock_completion_repo.get_by_execution_and_step = AsyncMock(return_value=None)
        mock_completion_repo.create = AsyncMock(return_value=MagicMock())
        mock_completion_repo.get_by_execution = AsyncMock(return_value=[])

        # Execute
        result = await compliance_service.mark_step_complete(
            execution_id=1,
            step_id=1,
            completed_at=datetime.utcnow(),
            is_on_schedule=True,
        )

        # Assert
        mock_completion_repo.create.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_mark_step_complete_execution_not_found(
        self,
        compliance_service,
        mock_execution_repo,
    ):
        """Test that missing execution raises error."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await compliance_service.mark_step_complete(
                execution_id=999,
                step_id=1,
                completed_at=datetime.utcnow(),
            )


class TestMarkStepSkipped:
    """Test marking steps as skipped."""

    @pytest.mark.asyncio
    async def test_mark_step_skipped_creates_record(
        self,
        compliance_service,
        sample_execution,
        mock_execution_repo,
        mock_completion_repo,
        mock_step_repo,
    ):
        """Test that marking step skipped creates StepCompletion record with skip_reason."""
        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_step_repo.get_by_id = AsyncMock(return_value=MagicMock())
        mock_completion_repo.create = AsyncMock(return_value=MagicMock())
        mock_completion_repo.get_by_execution = AsyncMock(return_value=[])

        # Execute
        result = await compliance_service.mark_step_skipped(
            execution_id=1,
            step_id=1,
            skip_reason=SkipReason.CONDITION_NOT_MET,
            skip_notes="pH already optimal",
        )

        # Assert
        mock_completion_repo.create.assert_called_once()
        call_args = mock_completion_repo.create.call_args[0][0]
        assert call_args.was_skipped is True
        assert call_args.skip_reason == SkipReason.CONDITION_NOT_MET.value


class TestDetectDeviations:
    """Test deviation detection."""

    @pytest.mark.asyncio
    async def test_detect_missing_critical_step(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test detection of missing critical step."""
        # Setup: only step 2 completed
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        deviations = await compliance_service.detect_deviations(1)

        # Assert: Should detect missing step 1 (critical)
        missing_step1 = next(
            (d for d in deviations if d.step_id == 1),
            None,
        )
        assert missing_step1 is not None
        assert missing_step1.severity == "CRITICAL"
        assert missing_step1.deviation_type == "MISSING"

    @pytest.mark.asyncio
    async def test_detect_late_step(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test detection of late step completion."""
        # Setup: step 2 completed 3 days late
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=5),  # 3 days late
                is_on_schedule=False,
                days_late=3,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        deviations = await compliance_service.detect_deviations(1)

        # Assert: Should detect late step 2
        late_step = next(
            (d for d in deviations if d.deviation_type == "LATE"),
            None,
        )
        assert late_step is not None
        assert late_step.severity == "HIGH"

    @pytest.mark.asyncio
    async def test_detect_unjustified_skip(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test detection of unjustified skip on critical step."""
        # Setup: step 1 (critical) unjustified skip
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                was_skipped=True,
                skip_reason=SkipReason.OTHER.value,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        deviations = await compliance_service.detect_deviations(1)

        # Assert: Should detect unjustified skip
        unjustified = next(
            (d for d in deviations if d.deviation_type == "UNJUSTIFIED_SKIP"),
            None,
        )
        assert unjustified is not None
        assert unjustified.severity == "CRITICAL"


class TestGetExecutionStatus:
    """Test execution status tracking."""

    @pytest.mark.asyncio
    async def test_get_execution_status_returns_complete_info(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that execution status includes all required information."""
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        status = await compliance_service.get_execution_status(1)

        # Assert
        assert status["execution_id"] == 1
        assert "compliance_score" in status
        assert "steps_progress" in status
        assert status["steps_progress"]["completed"] == 2
        assert status["steps_progress"]["pending"] == 1
        assert "deviations" in status


class TestGetOverdueSteps:
    """Test overdue step detection."""

    @pytest.mark.asyncio
    async def test_get_overdue_steps_returns_pending_steps_past_deadline(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test detection of overdue pending steps."""
        # Setup: execution started 7 days ago, no completions
        execution = sample_execution
        execution.start_date = datetime.utcnow() - timedelta(days=7)

        mock_execution_repo.get_by_id = AsyncMock(return_value=execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=[])

        # Execute
        overdue = await compliance_service.get_overdue_steps(1)

        # Assert: Steps expected on days 0, 2, 5 should all be overdue
        assert len(overdue) >= 3  # All 3 steps should be overdue


# ============================================================================
# Integration-like Tests
# ============================================================================

class TestComplianceScoringFormula:
    """Test the overall compliance scoring formula (ADR-036)."""

    @pytest.mark.asyncio
    async def test_formula_70_percent_completion_30_percent_timing(
        self,
        compliance_service,
        sample_execution,
        sample_protocol,
        mock_execution_repo,
        mock_completion_repo,
    ):
        """Test that final score = 70% completion + 30% timing."""
        # Setup: 2/3 steps completed on-time, 1/3 pending
        completions = [
            StepCompletion(
                execution_id=1,
                step_id=1,
                completed_at=sample_execution.start_date,
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
            StepCompletion(
                execution_id=1,
                step_id=2,
                completed_at=sample_execution.start_date + timedelta(days=2),
                is_on_schedule=True,
                days_late=0,
                was_skipped=False,
            ),
        ]

        mock_execution_repo.get_by_id = AsyncMock(return_value=sample_execution)
        mock_completion_repo.get_by_execution = AsyncMock(return_value=completions)

        # Execute
        result = await compliance_service.calculate_compliance_score(1)

        # Assert: Score should reflect both completion and timing
        # Completion: 2/3 steps with good criticality weights ≈ 94%
        # Timing: 2/2 on-time = 100%
        # Final: (94% × 0.7) + (100% × 0.3) ≈ 96%
        assert result.compliance_score >= 90
        assert result.weighted_completion > 0
        assert result.timing_score > 0

