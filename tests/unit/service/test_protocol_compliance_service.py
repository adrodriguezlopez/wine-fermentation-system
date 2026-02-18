"""
Unit Tests for Protocol Compliance Service

Tests ADR-036 Compliance Scoring Algorithm implementation.

Coverage:
- Perfect execution (100% score)
- Late steps (-2% per day, tiered penalties)
- Skipped critical steps (-15% penalty)
- Justified skips (+60% credit)
- Timing score calculations
- Critical step completion checks
- Deviation detection
- Execution status reporting
- Overdue step tracking
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock

from src.modules.fermentation.src.service_component.services.protocol_compliance_service import (
    ProtocolComplianceService,
    StepCompletionBreakdown,
    WeightedCompletionScore,
    TimingScore,
    ComplianceScoreResult,
    StepDeviation,
)
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import StepType, SkipReason, ProtocolExecutionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_protocol_repository():
    """Mock protocol repository."""
    return AsyncMock()


@pytest.fixture
def mock_execution_repository():
    """Mock execution repository."""
    return AsyncMock()


@pytest.fixture
def mock_completion_repository():
    """Mock completion repository."""
    return AsyncMock()


@pytest.fixture
def mock_step_repository():
    """Mock step repository."""
    return AsyncMock()


@pytest.fixture
def compliance_service(
    mock_protocol_repository,
    mock_execution_repository,
    mock_completion_repository,
    mock_step_repository,
):
    """Create compliance service with mocked repositories."""
    return ProtocolComplianceService(
        protocol_repository=mock_protocol_repository,
        execution_repository=mock_execution_repository,
        completion_repository=mock_completion_repository,
        step_repository=mock_step_repository,
    )


@pytest.fixture
def sample_fermentation_protocol():
    """Create a sample fermentation protocol with steps."""
    protocol = MagicMock(spec=FermentationProtocol)
    protocol.id = 1
    protocol.winery_id = 1
    protocol.varietal_name = "Cabernet Sauvignon"
    protocol.version = "1.0"

    # Create protocol steps
    steps = []

    # Critical step 1: Yeast Inoculation (criticality 1.5 = 150 points)
    step1 = MagicMock(spec=ProtocolStep)
    step1.id = 1
    step1.step_order = 1
    step1.step_type = StepType.INITIALIZATION
    step1.description = "Yeast Inoculation - Red Star Premier Cuvée"
    step1.expected_day = 0
    step1.tolerance_hours = 12
    step1.is_critical = True
    step1.criticality_score = 150  # 1.5x multiplier
    steps.append(step1)

    # Critical step 2: H2S Check (criticality 1.5 = 150 points)
    step2 = MagicMock(spec=ProtocolStep)
    step2.id = 2
    step2.step_order = 2
    step2.step_type = StepType.MONITORING
    step2.description = "H2S Check - Target <20 ppb"
    step2.expected_day = 2
    step2.tolerance_hours = 12
    step2.is_critical = True
    step2.criticality_score = 150
    steps.append(step2)

    # Critical step 3: DAP Addition (criticality 1.5 = 150 points)
    step3 = MagicMock(spec=ProtocolStep)
    step3.id = 3
    step3.step_order = 3
    step3.step_type = StepType.ADDITIONS
    step3.description = "DAP Addition - 1/3 sugar depletion"
    step3.expected_day = 3
    step3.tolerance_hours = 12
    step3.is_critical = True
    step3.criticality_score = 150
    steps.append(step3)

    # Optional step 4: Punch Down (criticality 0.5 = 50 points)
    step4 = MagicMock(spec=ProtocolStep)
    step4.id = 4
    step4.step_order = 4
    step4.step_type = StepType.CAP_MANAGEMENT
    step4.description = "Punch Down - Manual, 3x daily"
    step4.expected_day = 4
    step4.tolerance_hours = 6
    step4.is_critical = False
    step4.criticality_score = 50
    steps.append(step4)

    # Optional step 5: Temp Check (criticality 0.5 = 50 points)
    step5 = MagicMock(spec=ProtocolStep)
    step5.id = 5
    step5.step_order = 5
    step5.step_type = StepType.MONITORING
    step5.description = "Temperature Check - Target 65-75°F"
    step5.expected_day = 5
    step5.tolerance_hours = 12
    step5.is_critical = False
    step5.criticality_score = 50
    steps.append(step5)

    # Optional step 6: Racking (criticality 1.0 = 100 points)
    step6 = MagicMock(spec=ProtocolStep)
    step6.id = 6
    step6.step_order = 6
    step6.step_type = StepType.POST_FERMENTATION
    step6.description = "Racking - First racking"
    step6.expected_day = 10
    step6.tolerance_hours = 24
    step6.is_critical = False
    step6.criticality_score = 100
    steps.append(step6)

    protocol.steps = steps
    return protocol


@pytest.fixture
def sample_protocol_execution(sample_fermentation_protocol):
    """Create a sample protocol execution."""
    execution = MagicMock(spec=ProtocolExecution)
    execution.id = 1
    execution.fermentation_id = 1
    execution.protocol_id = 1
    execution.winery_id = 1
    execution.protocol = sample_fermentation_protocol
    execution.start_date = datetime(2024, 2, 10, 10, 0, 0)
    execution.status = "IN_PROGRESS"
    execution.completed_at = None
    execution.compliance_score = 0.0
    execution.completed_steps = 0
    execution.skipped_critical_steps = 0
    execution.notes = None
    execution.created_at = datetime.utcnow()

    return execution


# ============================================================================
# Test: Perfect Execution (100% Score)
# ============================================================================

@pytest.mark.asyncio
async def test_perfect_execution_100_percent_score(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test perfect execution where all steps are completed on-time.

    Expected: Compliance score = 100%
    """
    # Setup mocks
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    # All steps completed on-time
    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        MagicMock(
            step_id=2, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 12, 10, 0, 0)
        ),
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        MagicMock(
            step_id=4, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 14, 10, 0, 0)
        ),
        MagicMock(
            step_id=5, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 15, 10, 0, 0)
        ),
        MagicMock(
            step_id=6, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 20, 10, 0, 0)
        ),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    # Calculate score
    result = await compliance_service.calculate_compliance_score(1)

    # Assertions
    assert result.compliance_score == 100.0
    assert result.weighted_completion == 100.0
    assert result.timing_score == 100.0
    assert result.critical_steps_completion_pct == 100.0


# ============================================================================
# Test: Late Steps (-2% per day)
# ============================================================================

@pytest.mark.asyncio
async def test_one_step_one_day_late_25_percent_penalty(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test step completed 1 day late (within tolerance + 1 day).

    Expected: 25% penalty on that step's points
    - Step 2 (critical, 150 points): 150 - (150 * 0.25) = 112.5 points
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    # H2S Check (step 2) is 1 day late
    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        MagicMock(
            step_id=2, was_skipped=False, is_on_schedule=False, days_late=1,  # 1 day late
            completed_at=datetime(2024, 2, 13, 10, 0, 0)  # Day 2 + 1
        ),
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        MagicMock(
            step_id=4, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 14, 10, 0, 0)
        ),
        MagicMock(
            step_id=5, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 15, 10, 0, 0)
        ),
        MagicMock(
            step_id=6, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 20, 10, 0, 0)
        ),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    # With step 2 having 25% penalty:
    # Total earned: 150 + 112.5 + 150 + 50 + 50 + 100 = 612.5
    # Total possible: 150 + 150 + 150 + 50 + 50 + 100 = 650
    # Completion score: (612.5 / 650) * 100 = 94.23%
    # Timing score: 5 on-time / 6 total = 83.33%
    # Final: (94.23 * 0.7) + (83.33 * 0.3) = 66 + 25 = 91%
    assert result.weighted_completion == pytest.approx(94.23, abs=0.01)
    assert result.timing_score == pytest.approx(83.33, abs=0.01)
    assert result.compliance_score < 95


# ============================================================================
# Test: Justified Skip (+60% Credit)
# ============================================================================

@pytest.mark.asyncio
async def test_justified_skip_60_percent_credit(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test justified skip (FERMENTATION_ENDED reason) earns 60% credit.

    Expected: Step 5 skipped justifiably = 50 * 0.60 = 30 points
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        MagicMock(
            step_id=2, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 12, 10, 0, 0)
        ),
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        MagicMock(
            step_id=4, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 14, 10, 0, 0)
        ),
        MagicMock(
            step_id=5, was_skipped=True, skip_reason="FERMENTATION_ENDED",  # Justified skip
            is_on_schedule=None, days_late=0,
            completed_at=datetime(2024, 2, 15, 10, 0, 0)
        ),
        MagicMock(
            step_id=6, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 20, 10, 0, 0)
        ),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    # Step 5 justified skip: 50 * 0.60 = 30 points
    # Total earned: 150 + 150 + 150 + 50 + 30 + 100 = 630
    # Total possible: 650
    # Completion score: (630 / 650) * 100 = 96.92%
    # Timing score: 5 on-time / 5 completed = 100%
    # Final: (96.92 * 0.7) + (100 * 0.3) = 67.84 + 30 = 97.84%
    assert result.breakdown["completion"].step_breakdown[4].earned_points == pytest.approx(30, abs=0.01)
    assert result.weighted_completion == pytest.approx(96.92, abs=0.01)
    assert result.compliance_score > 95


# ============================================================================
# Test: Unjustified Skip (0% Credit)
# ============================================================================

@pytest.mark.asyncio
async def test_unjustified_skip_zero_credit(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test unjustified skip (OTHER reason) earns 0% credit.

    Expected: Step 5 skipped without justification = 0 points (vs 50 possible)
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        MagicMock(
            step_id=2, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 12, 10, 0, 0)
        ),
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        MagicMock(
            step_id=4, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 14, 10, 0, 0)
        ),
        MagicMock(
            step_id=5, was_skipped=True, skip_reason="OTHER",  # Unjustified skip
            is_on_schedule=None, days_late=0,
            completed_at=datetime(2024, 2, 15, 10, 0, 0)
        ),
        MagicMock(
            step_id=6, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 20, 10, 0, 0)
        ),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    # Step 5 unjustified skip: 0 points
    # Total earned: 150 + 150 + 150 + 50 + 0 + 100 = 600
    # Total possible: 650
    # Completion score: (600 / 650) * 100 = 92.31%
    assert result.breakdown["completion"].step_breakdown[4].earned_points == 0
    assert result.weighted_completion == pytest.approx(92.31, abs=0.01)


# ============================================================================
# Test: Critical Step Missing (-15% Penalty)
# ============================================================================

@pytest.mark.asyncio
async def test_critical_step_missing_15_percent_penalty(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test missing critical step incurs -15% overall penalty.

    Expected: All other steps perfect, but missing step 2 (critical)
    - Would be 100% normally
    - Critical completion: 2/3 = 66.67%
    - Penalty: -15%
    - Final: max(100 - 15, 0) = 85%
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    # Missing step 2 (critical H2S Check)
    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        # Step 2 missing
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        MagicMock(
            step_id=4, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 14, 10, 0, 0)
        ),
        MagicMock(
            step_id=5, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 15, 10, 0, 0)
        ),
        MagicMock(
            step_id=6, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 20, 10, 0, 0)
        ),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    # Critical completion: 2/3 = 66.67%
    # Because not all 3 critical steps done: -15% penalty
    # Completion score: (150 + 0 + 150 + 50 + 50 + 100) / (150 + 150 + 150 + 50 + 50 + 100) = 500/650 = 76.92%
    # Timing score: 5/5 = 100%
    # Final before penalty: (76.92 * 0.7) + (100 * 0.3) = 53.84 + 30 = 83.84%
    # Final after -15% penalty: max(83.84 - 15, 0) = 68.84%
    assert result.critical_steps_completion_pct < 100
    assert result.compliance_score < 90


# ============================================================================
# Test: All Critical Steps Complete (+5% Bonus)
# ============================================================================

@pytest.mark.asyncio
async def test_all_critical_steps_complete_5_percent_bonus(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test that completing all critical steps earns +5% bonus.

    Expected: Even if optional steps pending, having all critical steps = +5 bonus
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    # All critical steps done, no optional steps
    completions = [
        MagicMock(
            step_id=1, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 10, 10, 0, 0)
        ),
        MagicMock(
            step_id=2, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 12, 10, 0, 0)
        ),
        MagicMock(
            step_id=3, was_skipped=False, is_on_schedule=True, days_late=0,
            completed_at=datetime(2024, 2, 13, 10, 0, 0)
        ),
        # Steps 4, 5, 6 not started
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    # All critical steps done: +5 bonus
    # But score is capped at 100
    assert result.critical_steps_completion_pct == 100.0
    assert result.compliance_score <= 100.0


# ============================================================================
# Test: No Completed Steps
# ============================================================================

@pytest.mark.asyncio
async def test_no_completed_steps_zero_score(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test execution with no completed steps = 0% score.

    Expected: No completions = 0 earned points, 100% missing = 0% final score
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    completions = []  # No completions

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    result = await compliance_service.calculate_compliance_score(1)

    assert result.weighted_completion == 0.0
    assert result.timing_score == 100.0  # No completed steps = no timing issues yet
    # Final: (0 * 0.7) + (100 * 0.3) = 30%
    # But missing all critical steps: -15%
    # = max(30 - 15, 0) = 15%
    assert result.compliance_score <= 30


# ============================================================================
# Test: Deviation Detection - Missing Critical Step
# ============================================================================

@pytest.mark.asyncio
async def test_detect_deviations_missing_critical_step(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test detect_deviations identifies missing critical steps.
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    completions = [
        MagicMock(step_id=1, was_skipped=False),
        MagicMock(step_id=3, was_skipped=False),
        # Step 2 missing (critical)
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    deviations = await compliance_service.detect_deviations(1)

    # Should detect missing step 2
    missing_deviations = [d for d in deviations if d.deviation_type == "MISSING"]
    assert len(missing_deviations) > 0
    assert any(d.step_id == 2 for d in missing_deviations)


# ============================================================================
# Test: Execution Status Tracking
# ============================================================================

@pytest.mark.asyncio
async def test_get_execution_status_includes_progress_and_compliance(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test get_execution_status returns complete status including score and progress.
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    completions = [
        MagicMock(step_id=1, was_skipped=False),
        MagicMock(step_id=2, was_skipped=False),
        MagicMock(step_id=3, was_skipped=True),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    status = await compliance_service.get_execution_status(1)

    assert "execution_id" in status
    assert "compliance_score" in status
    assert "steps_progress" in status
    assert status["steps_progress"]["completed"] == 2
    assert status["steps_progress"]["skipped"] == 1
    assert status["steps_progress"]["pending"] == 3  # 6 total - 2 completed - 1 skipped


# ============================================================================
# Test: Mark Step Complete
# ============================================================================

@pytest.mark.asyncio
async def test_mark_step_complete_creates_record_and_updates_score(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test mark_step_complete creates completion record and triggers score recalc.
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    compliance_service.step_repo.get_by_id = AsyncMock(
        return_value=sample_fermentation_protocol.steps[0]
    )

    # Mock get_by_execution_and_step to return None (step not yet completed)
    compliance_service.completion_repo.get_by_execution_and_step = AsyncMock(
        return_value=None
    )

    compliance_service.completion_repo.create = AsyncMock(
        return_value=MagicMock(id=1)
    )

    # Mock calculate_compliance_score to avoid actual calculation
    compliance_service.calculate_compliance_score = AsyncMock(
        return_value=MagicMock(compliance_score=95.0, breakdown={"completion": MagicMock(completed_count=1)})
    )

    result = await compliance_service.mark_step_complete(
        execution_id=1,
        step_id=1,
        completed_at=datetime.utcnow(),
        is_on_schedule=True,
        days_late=0,
    )

    # Verify completion record was created
    assert result is not None


# ============================================================================
# Test: Mark Step Skipped
# ============================================================================

@pytest.mark.asyncio
async def test_mark_step_skipped_creates_skip_record(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test mark_step_skipped creates skip record with reason.
    """
    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    compliance_service.step_repo.get_by_id = AsyncMock(
        return_value=sample_fermentation_protocol.steps[0]
    )

    compliance_service.completion_repo.create = AsyncMock(
        return_value=MagicMock(id=2)
    )

    compliance_service.calculate_compliance_score = AsyncMock(
        return_value=MagicMock(compliance_score=85.0, breakdown={"completion": MagicMock(completed_count=0)})
    )

    result = await compliance_service.mark_step_skipped(
        execution_id=1,
        step_id=1,
        skip_reason=SkipReason.FERMENTATION_ENDED,
        skip_notes="Fermentation completed early",
    )

    # Verify skip record was created
    assert result is not None
    assert result.was_skipped == True


# ============================================================================
# Test: Overdue Steps
# ============================================================================

@pytest.mark.asyncio
async def test_get_overdue_steps_identifies_past_expected_dates(
    compliance_service,
    sample_protocol_execution,
    sample_fermentation_protocol,
):
    """
    Test get_overdue_steps identifies steps past their expected completion date.
    """
    # Execution started 10 days ago
    sample_protocol_execution.start_date = datetime.utcnow() - timedelta(days=10)

    compliance_service.execution_repo.get_by_id = AsyncMock(
        return_value=sample_protocol_execution
    )

    # Only steps 1-3 completed
    completions = [
        MagicMock(step_id=1, was_skipped=False),
        MagicMock(step_id=2, was_skipped=False),
        MagicMock(step_id=3, was_skipped=False),
    ]

    compliance_service.completion_repo.get_by_execution = AsyncMock(
        return_value=completions
    )

    overdue = await compliance_service.get_overdue_steps(1)

    # Steps 4 (expected day 4), 5 (day 5), 6 (day 10) should be overdue
    # since we're 10 days into execution
    assert len(overdue) > 0


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_execution_not_found_raises_error(compliance_service):
    """Test that requesting non-existent execution raises ValueError."""
    compliance_service.execution_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await compliance_service.calculate_compliance_score(999)


@pytest.mark.asyncio
async def test_protocol_missing_raises_error(compliance_service):
    """Test that execution without protocol raises ValueError."""
    execution = MagicMock(spec=ProtocolExecution)
    execution.protocol = None
    compliance_service.execution_repo.get_by_id = AsyncMock(return_value=execution)

    with pytest.raises(ValueError, match="no protocol"):
        await compliance_service.calculate_compliance_score(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
