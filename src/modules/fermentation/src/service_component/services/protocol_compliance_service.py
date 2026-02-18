"""
Protocol Compliance Scoring Service

Implements ADR-036: Compliance Scoring Algorithm.

Provides deterministic, explainable compliance scoring based on:
- Weighted completion score (70% of final score)
- Timing score (30% of final score)
- Criticality-weighted steps
- Late execution penalties
- Justified skip credits

Performance Target: <100ms per calculation
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import SkipReason
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.repository_component.step_completion_repository import StepCompletionRepository


# ============================================================================
# Data Models for Compliance Scoring
# ============================================================================

@dataclass
class StepCompletionBreakdown:
    """Detailed breakdown of points earned for a single step."""
    step_id: int
    step_type: str
    earned_points: float
    possible_points: float
    notes: str
    completed_at: Optional[datetime] = None
    days_late: int = 0
    was_skipped: bool = False


@dataclass
class WeightedCompletionScore:
    """Result of weighted completion score calculation."""
    score: float  # 0-100
    step_breakdown: List[StepCompletionBreakdown]
    total_earned: float
    total_possible: float
    completed_count: int
    skipped_count: int
    pending_count: int


@dataclass
class TimingScore:
    """Result of timing score calculation."""
    score: float  # 0-100 (percentage of on-time completions)
    on_time_count: int
    late_count: int
    total_completed: int


@dataclass
class ComplianceScoreResult:
    """Final compliance score with detailed breakdown."""
    compliance_score: float  # 0-100
    weighted_completion: float  # 0-100
    timing_score: float  # 0-100
    critical_steps_completion_pct: float  # 0-100
    breakdown: Dict  # {completion: WeightedCompletionScore, timing: TimingScore}
    calculation_timestamp: datetime


@dataclass
class StepDeviation:
    """Represents a deviation from expected protocol execution."""
    step_id: int
    step_type: str
    description: str
    deviation_type: str  # "MISSING", "LATE", "OUT_OF_SEQUENCE"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    details: str


# ============================================================================
# Justified Skip Reasons
# ============================================================================

# These skip reasons earn 60% credit
JUSTIFIED_SKIP_REASONS = {
    SkipReason.CONDITION_NOT_MET,      # pH already optimal, fermentation ended, etc.
    SkipReason.FERMENTATION_ENDED,     # Early fermentation completion
    SkipReason.WINEMAKER_DECISION,     # Expert judgment override
}

# These skip reasons earn 0% credit
UNJUSTIFIED_SKIP_REASONS = {
    SkipReason.EQUIPMENT_FAILURE,      # Equipment failure (should have alternative)
    SkipReason.FERMENTATION_FAILED,    # Fermentation failure (unrecoverable)
    SkipReason.REPLACED_BY_ALTERNATIVE,# Replaced by alternative step (already accounted)
    SkipReason.OTHER,                  # Unexplained skip
}


# ============================================================================
# Protocol Compliance Service
# ============================================================================

class ProtocolComplianceService:
    """
    Service for calculating compliance scores for protocol executions.
    
    Implements ADR-036 compliance scoring algorithm:
    - Deterministic: Same inputs always produce same output
    - Explainable: Can detail why score is X, not Y+1
    - Real-time: Score updates as steps complete
    - Actionable: Breakdown shows which steps are dragging down score
    """

    def __init__(
        self,
        protocol_repository: FermentationProtocolRepository,
        execution_repository: ProtocolExecutionRepository,
        completion_repository: StepCompletionRepository,
        step_repository: ProtocolStepRepository,
    ):
        """Initialize service with repository dependencies."""
        self.protocol_repo = protocol_repository
        self.execution_repo = execution_repository
        self.completion_repo = completion_repository
        self.step_repo = step_repository

    # ========================================================================
    # Primary Public Method: Calculate Compliance Score
    # ========================================================================

    async def calculate_compliance_score(
        self,
        execution_id: int,
    ) -> ComplianceScoreResult:
        """
        Calculate final compliance score for a protocol execution.

        Formula:
            COMPLIANCE_SCORE = (WEIGHTED_COMPLETION_SCORE × 0.7) + (TIMING_SCORE × 0.3)

        Plus adjustments:
            - All critical steps done: +5 bonus (capped at 100)
            - Missing critical steps: -15 penalty (floor at 0)

        Args:
            execution_id: ID of ProtocolExecution to score

        Returns:
            ComplianceScoreResult with breakdown

        Raises:
            ValueError: If execution not found or protocol missing
        """
        # Load execution and protocol
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        protocol = execution.protocol
        if not protocol:
            raise ValueError(
                f"ProtocolExecution {execution_id} has no protocol assigned"
            )

        # Step 1: Calculate weighted completion score
        completion_score_data = await self._calculate_weighted_completion_score(
            protocol, execution
        )

        # Step 2: Calculate timing score
        timing_score_data = await self._calculate_timing_score(execution)

        # Step 3: Combine into final score
        final_score = (
            (completion_score_data.score * 0.70) +
            (timing_score_data.score * 0.30)
        )

        # Step 4: Apply critical steps adjustments
        critical_steps_completion_pct = await self._calculate_critical_completion_pct(
            protocol, execution
        )

        # Adjust for critical step completion
        if critical_steps_completion_pct == 100:
            # All critical steps done: +5 bonus
            final_score = min(final_score + 5, 100)
        elif critical_steps_completion_pct < 100:
            # Missing critical steps: -15 penalty
            final_score = max(final_score - 15, 0)

        result = ComplianceScoreResult(
            compliance_score=round(min(final_score, 100), 2),
            weighted_completion=round(completion_score_data.score, 2),
            timing_score=round(timing_score_data.score, 2),
            critical_steps_completion_pct=round(critical_steps_completion_pct, 2),
            breakdown={
                "completion": completion_score_data,
                "timing": timing_score_data,
            },
            calculation_timestamp=datetime.utcnow(),
        )

        return result

    # ========================================================================
    # Step Completion Tracking
    # ========================================================================

    async def mark_step_complete(
        self,
        execution_id: int,
        step_id: int,
        completed_at: datetime,
        completed_by_user_id: Optional[int] = None,
        verified_by_user_id: Optional[int] = None,
        notes: Optional[str] = None,
        is_on_schedule: bool = True,
        days_late: int = 0,
    ) -> StepCompletion:
        """
        Mark a protocol step as completed and recalculate compliance score.

        Args:
            execution_id: ID of execution
            step_id: ID of step being completed
            completed_at: When the step was actually completed
            completed_by_user_id: User who performed the step
            verified_by_user_id: User who verified completion
            notes: Optional completion notes
            is_on_schedule: Was step completed within tolerance window?
            days_late: Days after expected date (0 if on-time)

        Returns:
            Created StepCompletion record

        Raises:
            ValueError: If execution or step not found, or step already completed
        """
        # Validate execution exists
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        # Validate step exists
        step = await self._get_step(step_id)
        if not step:
            raise ValueError(f"ProtocolStep {step_id} not found")

        # Check if step already completed
        existing = await self.completion_repo.get_by_execution_and_step(
            execution_id, step_id
        )
        if existing and not existing.was_skipped:
            raise ValueError(
                f"Step {step_id} already completed for execution {execution_id}"
            )

        # Create completion record
        completion = StepCompletion(
            execution_id=execution_id,
            step_id=step_id,
            completed_at=completed_at,
            completed_by_user_id=completed_by_user_id,
            verified_by_user_id=verified_by_user_id,
            notes=notes,
            is_on_schedule=is_on_schedule,
            days_late=days_late,
            was_skipped=False,
            skip_reason=None,
        )

        # Save completion record
        await self.completion_repo.create(completion)
        await self.execution_repo.session.commit()

        # Recalculate and update execution compliance score
        await self._update_execution_compliance_score(execution_id)

        return completion

    async def mark_step_skipped(
        self,
        execution_id: int,
        step_id: int,
        skip_reason: SkipReason,
        skip_notes: Optional[str] = None,
        completed_by_user_id: Optional[int] = None,
        verified_by_user_id: Optional[int] = None,
    ) -> StepCompletion:
        """
        Mark a protocol step as skipped (with reason) and recalculate compliance score.

        Args:
            execution_id: ID of execution
            step_id: ID of step being skipped
            skip_reason: Why was the step skipped?
            skip_notes: Detailed justification
            completed_by_user_id: Who made the decision to skip
            verified_by_user_id: Who approved the skip

        Returns:
            Created StepCompletion record with skip_reason

        Raises:
            ValueError: If execution or step not found
        """
        # Validate execution exists
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        # Validate step exists
        step = await self._get_step(step_id)
        if not step:
            raise ValueError(f"ProtocolStep {step_id} not found")

        # Create skip record
        completion = StepCompletion(
            execution_id=execution_id,
            step_id=step_id,
            completed_at=datetime.utcnow(),
            was_skipped=True,
            skip_reason=skip_reason.value,
            skip_notes=skip_notes,
            completed_by_user_id=completed_by_user_id,
            verified_by_user_id=verified_by_user_id,
            is_on_schedule=None,
            days_late=0,
        )

        # Save skip record
        await self.completion_repo.create(completion)
        await self.execution_repo.session.commit()

        # Recalculate and update execution compliance score
        await self._update_execution_compliance_score(execution_id)

        return completion

    # ========================================================================
    # Deviation Detection
    # ========================================================================

    async def detect_deviations(
        self,
        execution_id: int,
    ) -> List[StepDeviation]:
        """
        Detect deviations from expected protocol execution.

        Identifies:
        - Missing critical steps
        - Steps completed after deadline
        - Steps completed out of order
        - Unjustified skips

        Args:
            execution_id: ID of execution to analyze

        Returns:
            List of StepDeviation objects

        Raises:
            ValueError: If execution not found
        """
        # Load execution and protocol
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        protocol = execution.protocol
        if not protocol:
            raise ValueError(f"Execution {execution_id} has no protocol")

        deviations: List[StepDeviation] = []

        # Get all completions for this execution
        completions = await self.completion_repo.get_by_execution(execution_id)
        completed_step_ids = {
            c.step_id for c in completions
            if not c.was_skipped or c.skip_reason in [r.value for r in JUSTIFIED_SKIP_REASONS]
        }

        for step in protocol.steps:
            # Check if critical step is missing
            if step.is_critical and step.id not in completed_step_ids:
                # Check if it's an unjustified skip
                skip_record = next(
                    (c for c in completions if c.step_id == step.id and c.was_skipped),
                    None
                )
                if skip_record:
                    if skip_record.skip_reason not in [
                        r.value for r in JUSTIFIED_SKIP_REASONS
                    ]:
                        deviations.append(
                            StepDeviation(
                                step_id=step.id,
                                step_type=step.step_type.value,
                                description=step.description,
                                deviation_type="UNJUSTIFIED_SKIP",
                                severity="CRITICAL",
                                details=f"Critical step skipped without justification: {skip_record.skip_reason}",
                            )
                        )
                else:
                    deviations.append(
                        StepDeviation(
                            step_id=step.id,
                            step_type=step.step_type.value,
                            description=step.description,
                            deviation_type="MISSING",
                            severity="CRITICAL",
                            details="Critical step not completed",
                        )
                    )

            # Check if step was late
            completion = next(
                (c for c in completions if c.step_id == step.id),
                None
            )
            if completion and not completion.was_skipped and not completion.is_on_schedule:
                severity = "HIGH" if completion.days_late > 2 else "MEDIUM"
                deviations.append(
                    StepDeviation(
                        step_id=step.id,
                        step_type=step.step_type.value,
                        description=step.description,
                        deviation_type="LATE",
                        severity=severity,
                        details=f"Step completed {completion.days_late} days late",
                    )
                )

        return deviations

    # ========================================================================
    # Execution Status Tracking
    # ========================================================================

    async def get_execution_status(
        self,
        execution_id: int,
    ) -> Dict:
        """
        Get complete execution status including progress and compliance.

        Args:
            execution_id: ID of execution

        Returns:
            Dictionary with:
            - execution details (status, start_date, etc.)
            - compliance_score
            - steps_progress (completed, skipped, pending)
            - deviations (if any)

        Raises:
            ValueError: If execution not found
        """
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        # Calculate current compliance score
        score_result = await self.calculate_compliance_score(execution_id)

        # Get completions
        completions = await self.completion_repo.get_by_execution(execution_id)
        completed_count = sum(1 for c in completions if not c.was_skipped)
        skipped_count = sum(1 for c in completions if c.was_skipped)
        pending_count = len(execution.protocol.steps) - completed_count - skipped_count

        # Detect deviations
        deviations = await self.detect_deviations(execution_id)

        return {
            "execution_id": execution_id,
            "status": execution.status,
            "start_date": execution.start_date,
            "completed_at": execution.completed_at,
            "compliance_score": score_result.compliance_score,
            "weighted_completion": score_result.weighted_completion,
            "timing_score": score_result.timing_score,
            "critical_completion_pct": score_result.critical_steps_completion_pct,
            "steps_progress": {
                "completed": completed_count,
                "skipped": skipped_count,
                "pending": pending_count,
                "total": len(execution.protocol.steps),
            },
            "deviations": [
                {
                    "step_id": d.step_id,
                    "type": d.deviation_type,
                    "severity": d.severity,
                    "details": d.details,
                }
                for d in deviations
            ],
        }

    async def get_overdue_steps(self, execution_id: int) -> List[Dict]:
        """
        Get list of steps that are currently overdue.

        Args:
            execution_id: ID of execution

        Returns:
            List of overdue step details

        Raises:
            ValueError: If execution not found
        """
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"ProtocolExecution {execution_id} not found")

        protocol = execution.protocol
        completions = await self.completion_repo.get_by_execution(execution_id)
        completed_step_ids = {c.step_id for c in completions}

        overdue_steps = []
        now = datetime.utcnow()

        for step in protocol.steps:
            # Skip if already completed
            if step.id in completed_step_ids:
                continue

            # Calculate expected completion date
            expected_date = execution.start_date.replace(hour=0, minute=0, second=0)
            expected_date = expected_date.replace(
                day=expected_date.day + step.expected_day
            )

            # Check if overdue
            if now > expected_date:
                days_overdue = (now - expected_date).days
                overdue_steps.append(
                    {
                        "step_id": step.id,
                        "step_type": step.step_type.value,
                        "description": step.description,
                        "expected_date": expected_date,
                        "days_overdue": days_overdue,
                        "is_critical": step.is_critical,
                    }
                )

        return overdue_steps

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _calculate_weighted_completion_score(
        self,
        protocol: FermentationProtocol,
        execution: ProtocolExecution,
    ) -> WeightedCompletionScore:
        """
        Calculate weighted completion score (0-100).

        For each step:
        - Base points: 100 × (criticality_score / 100)
        - Completed on-time: 100% of points
        - Completed late (within tolerance): 90% of points
        - Completed late (1+ days): 75% of points
        - Completed late (2+ days): 50% of points
        - Justified skip: 60% of points
        - Unjustified skip: 0% of points
        - Not completed: 0% of points
        """
        step_results = []
        total_earned = 0.0
        total_possible = 0.0
        completed_count = 0
        skipped_count = 0

        # Get all completions for this execution
        completions = await self.completion_repo.get_by_execution(execution.id)
        completion_map = {c.step_id: c for c in completions}

        for step in protocol.steps:
            completion = completion_map.get(step.id)
            result = await self._calculate_step_completion_points(step, completion)

            step_results.append(result)
            total_earned += result.earned_points
            total_possible += result.possible_points

            if completion:
                if completion.was_skipped:
                    skipped_count += 1
                else:
                    completed_count += 1

        pending_count = len(protocol.steps) - completed_count - skipped_count

        # Calculate final score
        if total_possible == 0:
            score = 0
        else:
            score = (total_earned / total_possible) * 100

        return WeightedCompletionScore(
            score=round(score, 2),
            step_breakdown=step_results,
            total_earned=round(total_earned, 2),
            total_possible=round(total_possible, 2),
            completed_count=completed_count,
            skipped_count=skipped_count,
            pending_count=pending_count,
        )

    async def _calculate_step_completion_points(
        self,
        step: ProtocolStep,
        completion: Optional[StepCompletion],
    ) -> StepCompletionBreakdown:
        """Calculate points earned for a single step."""
        # Base points from criticality
        criticality_multiplier = step.criticality_score / 100.0
        possible_points = 100 * criticality_multiplier

        # Step not completed
        if completion is None:
            return StepCompletionBreakdown(
                step_id=step.id,
                step_type=step.step_type.value,
                earned_points=0,
                possible_points=possible_points,
                notes="Step not completed",
                was_skipped=False,
            )

        # Step was skipped
        if completion.was_skipped:
            skip_reason = SkipReason(completion.skip_reason)
            if skip_reason in JUSTIFIED_SKIP_REASONS:
                earned = possible_points * 0.60
                return StepCompletionBreakdown(
                    step_id=step.id,
                    step_type=step.step_type.value,
                    earned_points=earned,
                    possible_points=possible_points,
                    notes=f"Justifiably skipped ({skip_reason.value}): 60% credit",
                    was_skipped=True,
                )
            else:
                return StepCompletionBreakdown(
                    step_id=step.id,
                    step_type=step.step_type.value,
                    earned_points=0,
                    possible_points=possible_points,
                    notes=f"Skipped without justification ({skip_reason.value})",
                    was_skipped=True,
                )

        # Step was completed
        earned_points = possible_points

        # Apply timing penalty
        if not completion.is_on_schedule:
            days_late = completion.days_late or 0
            tolerance_days = (step.tolerance_hours or 0) / 24.0

            if days_late <= tolerance_days:
                # Slightly late but within extended tolerance: 10% penalty
                timing_penalty = possible_points * 0.10
            elif days_late <= (tolerance_days + 1):
                # 1 day past tolerance: 25% penalty
                timing_penalty = possible_points * 0.25
            else:
                # 2+ days late: 50% penalty
                timing_penalty = min(possible_points * 0.50, possible_points)

            earned_points -= timing_penalty

        earned_points = max(earned_points, 0)

        return StepCompletionBreakdown(
            step_id=step.id,
            step_type=step.step_type.value,
            earned_points=earned_points,
            possible_points=possible_points,
            completed_at=completion.completed_at,
            days_late=completion.days_late or 0,
            notes=f"On-time: {completion.is_on_schedule}; Days late: {completion.days_late or 0}",
            was_skipped=False,
        )

    async def _calculate_timing_score(
        self,
        execution: ProtocolExecution,
    ) -> TimingScore:
        """
        Calculate timing score (percentage of on-time completions).

        Only counts non-skipped steps.
        """
        completions = await self.completion_repo.get_by_execution(execution.id)
        non_skipped = [c for c in completions if not c.was_skipped]

        if not non_skipped:
            return TimingScore(
                score=100,  # No completed steps = no timing issues yet
                on_time_count=0,
                late_count=0,
                total_completed=0,
            )

        on_time_count = sum(1 for c in non_skipped if c.is_on_schedule)
        late_count = len(non_skipped) - on_time_count

        score = (on_time_count / len(non_skipped)) * 100 if non_skipped else 0

        return TimingScore(
            score=round(score, 2),
            on_time_count=on_time_count,
            late_count=late_count,
            total_completed=len(non_skipped),
        )

    async def _calculate_critical_completion_pct(
        self,
        protocol: FermentationProtocol,
        execution: ProtocolExecution,
    ) -> float:
        """Calculate percentage of critical steps that are completed (not skipped)."""
        completions = await self.completion_repo.get_by_execution(execution.id)
        critical_steps = [s for s in protocol.steps if s.is_critical]

        if not critical_steps:
            return 100.0

        completed_critical = sum(
            1 for step in critical_steps
            if any(
                c.step_id == step.id and not c.was_skipped
                for c in completions
            )
        )

        return (completed_critical / len(critical_steps)) * 100

    async def _update_execution_compliance_score(self, execution_id: int) -> None:
        """
        Recalculate and persist compliance score for an execution.

        Called after step completion/skip.
        """
        score_result = await self.calculate_compliance_score(execution_id)

        execution = await self.execution_repo.get_by_id(execution_id)
        if execution:
            execution.compliance_score = score_result.compliance_score
            execution.completed_steps = score_result.breakdown["completion"].completed_count
            await self.execution_repo.update(execution)
            await self.execution_repo.session.commit()

    async def _get_step(self, step_id: int) -> Optional[ProtocolStep]:
        """Helper to fetch a step by ID."""
        return await self.step_repo.get_by_id(step_id)
