# ADR-038: Protocol Deviation Detection Strategy

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team  
**Related ADRs**: ADR-036 (Compliance Scoring), ADR-037 (Analysis Integration)  
**Timeline Context**: Phase 2 implementation (Week 5-6)

---

## Context and Problem Statement

From the AI Enologist analysis, deviations fall into 3 categories:

1. **Timing Deviations**: Step completed late
   - H2S Check 2 days late (when tolerance = ±6 hours) → CRITICAL
   - Racking 3 days late (tolerance = ±5 days) → ACCEPTABLE

2. **Skipped Deviations**: Step not completed
   - Justified: "H2S not detected, no point checking" → 60% score credit
   - Unjustified: "Forgot to punch down" → 0% score credit

3. **Execution Deviations**: Conditions not met
   - Step says "Add DAP at 1/3 sugar depletion" but actually added at 1/4 → DATA QUALITY ISSUE

The system must:
- **Detect** deviations in real-time
- **Alert** winemaker to significant deviations
- **Store** justifications for audit trail
- **Learn** from patterns (via Analysis Engine)

---

## Decision

### Deviation Detection Framework

#### 1. Timing Deviation Detection

```python
def detect_timing_deviation(
    step: ProtocolStep,
    completion: StepCompletion
) -> Optional[TimingDeviation]:
    """
    Determine if step completed outside acceptable window.
    
    Returns deviation if exists, None if on-time.
    """
    
    # Expected completion date
    expected_date = execution.start_date + timedelta(days=step.expected_day)
    expected_window_start = expected_date - timedelta(hours=step.tolerance_hours)
    expected_window_end = expected_date + timedelta(hours=step.tolerance_hours)
    
    # Actual completion date
    actual_date = completion.completed_at
    
    # Case 1: Completed on-time (within window)
    if expected_window_start <= actual_date <= expected_window_end:
        return None  # No deviation
    
    # Case 2: Completed EARLY (before window)
    if actual_date < expected_window_start:
        days_early = (expected_window_start - actual_date).days
        
        # Minor early completion (<1 day) is usually fine
        if days_early < 1:
            return None
        
        # Significant early completion (e.g., 3 days early) is deviation
        return TimingDeviation(
            type=DeviationType.EARLY,
            step_id=step.id,
            expected_date=expected_date,
            actual_date=actual_date,
            days_variance=days_early,
            severity=DeviationSeverity.MEDIUM,
            reason_code="EARLY_COMPLETION",
            description=f"Step completed {days_early} days early"
        )
    
    # Case 3: Completed LATE (after window)
    if actual_date > expected_window_end:
        days_late = (actual_date - expected_window_end).days
        
        # Criticality determines severity
        if step.is_critical:
            if days_late <= 1:
                severity = DeviationSeverity.HIGH
            elif days_late <= 3:
                severity = DeviationSeverity.CRITICAL
            else:
                severity = DeviationSeverity.CRITICAL
        else:
            # Non-critical steps have lower severity for same lateness
            if days_late <= 3:
                severity = DeviationSeverity.LOW
            else:
                severity = DeviationSeverity.MEDIUM
        
        return TimingDeviation(
            type=DeviationType.LATE,
            step_id=step.id,
            expected_date=expected_date,
            actual_date=actual_date,
            days_variance=days_late,
            severity=severity,
            reason_code="LATE_COMPLETION",
            description=f"Step completed {days_late} days late"
        )


# Schema
class TimingDeviation:
    id: int
    execution_id: int
    type: DeviationType  # EARLY, LATE
    step_id: int
    expected_date: datetime
    actual_date: datetime
    days_variance: int
    severity: DeviationSeverity  # LOW, MEDIUM, HIGH, CRITICAL
    reason_code: str
    description: str
    winemaker_acknowledgment: Optional[str]  # "pH was correct, no need to wait"
    created_at: datetime
    acknowledged_at: Optional[datetime]
```

#### 2. Skip Deviation Detection

```python
def detect_skip_deviation(
    step: ProtocolStep,
    completion: StepCompletion
) -> Optional[SkipDeviation]:
    """
    Determine if skip is justified or concerning.
    """
    
    skip_reason = completion.skip_reason
    
    # Justified skips (don't trigger deviation)
    justified_reasons = [
        SkipReason.CONDITION_NOT_MET,       # "pH already optimal"
        SkipReason.FERMENTATION_ENDED,      # "Brix now negative"
        SkipReason.WINEMAKER_DECISION,      # Expert judgment
    ]
    
    if skip_reason in justified_reasons:
        return None  # No deviation, skip is acceptable
    
    # Unjustified skips trigger deviation
    unjustified_reasons = [
        SkipReason.EQUIPMENT_FAILURE,       # Should reschedule
        SkipReason.FERMENTATION_FAILED,     # Loss event
        SkipReason.REPLACED_BY_ALTERNATIVE, # Protocol deviation
        SkipReason.OTHER,                   # Unknown reason
    ]
    
    if skip_reason in unjustified_reasons:
        severity = DeviationSeverity.CRITICAL if step.is_critical else DeviationSeverity.MEDIUM
        
        return SkipDeviation(
            execution_id=execution.id,
            step_id=step.id,
            skip_reason=skip_reason,
            severity=severity,
            description=f"Step skipped: {skip_reason.value}",
            skip_notes=completion.skip_notes,
            requires_investigation=True
        )
    
    return None
```

#### 3. Execution Quality Deviation

```python
def detect_execution_quality_deviation(
    step: ProtocolStep,
    completion: StepCompletion
) -> Optional[ExecutionDeviation]:
    """
    Detect if step completed but with quality issues.
    Example: "Add DAP at 1/3 sugar depletion" but actually added at 1/4
    
    This requires winemaker notes or historical data comparison.
    """
    
    # Check completion notes for quality indicators
    notes = completion.notes or ""
    
    # Pattern: If step is BRIX_READING and notes are empty, might be issue
    if step.step_type == StepType.BRIX_READING and not notes:
        return ExecutionDeviation(
            execution_id=execution.id,
            step_id=step.id,
            type="MISSING_DATA",
            severity=DeviationSeverity.LOW,
            description="BRIX reading completed but no value recorded",
            resolution="Ask winemaker to enter BRIX value"
        )
    
    # Pattern: If step is H2S_CHECK but adjacent TEMPERATURE_CHECK missed
    # (might indicate rushed inspection)
    if step.step_type == StepType.H2S_CHECK:
        temp_check_step = find_nearby_step(step, StepType.TEMPERATURE_CHECK, days=1)
        if temp_check_step and temp_check_step.was_skipped:
            return ExecutionDeviation(
                execution_id=execution.id,
                step_id=step.id,
                type="PATTERN_ANOMALY",
                severity=DeviationSeverity.MEDIUM,
                description="H2S check completed but temp check nearby was skipped",
                resolution="Verify both inspections were thorough"
            )
    
    return None
```

---

### Real-Time Deviation Workflow

```python
# service/protocol_service.py

def record_step_completion(
    execution_id: int,
    step_id: int,
    completed_at: datetime,
    notes: Optional[str] = None,
    user_id: int = None
) -> StepCompletion:
    """
    Complete a step and detect deviations in real-time.
    """
    
    execution = ProtocolExecution.get(id=execution_id)
    step = ProtocolStep.get(id=step_id)
    
    # Record completion
    completion = StepCompletion.create(
        execution_id=execution_id,
        step_id=step_id,
        completed_at=completed_at,
        notes=notes,
        verified_by_user_id=user_id
    )
    
    # Detect timing deviations
    timing_dev = detect_timing_deviation(step, completion)
    if timing_dev:
        timing_dev.save()
        logger.warning(f"Timing deviation detected: {timing_dev.description}")
        
        # If critical and late, alert immediately
        if timing_dev.severity == DeviationSeverity.CRITICAL:
            send_alert(
                user_id=execution.fermentation.created_by_user_id,
                message=f"CRITICAL: {timing_dev.description}",
                alert_type="PROTOCOL_DEVIATION"
            )
    
    # Detect skip deviations
    if completion.was_skipped:
        skip_dev = detect_skip_deviation(step, completion)
        if skip_dev:
            skip_dev.save()
            logger.warning(f"Skip deviation detected: {skip_dev.description}")
    
    # Detect execution quality issues
    exec_dev = detect_execution_quality_deviation(step, completion)
    if exec_dev:
        exec_dev.save()
        logger.info(f"Execution quality issue: {exec_dev.description}")
    
    # Recalculate compliance score
    execution.compliance_score = calculate_compliance_score(execution)
    execution.completed_steps = count_completed(execution)
    execution.save()
    
    # Trigger Analysis recalibration (async)
    emit_event("STEP_COMPLETED", {
        "execution_id": execution_id,
        "step_id": step_id,
        "completion_id": completion.id,
        "deviations_found": [
            timing_dev.id if timing_dev else None,
            skip_dev.id if skip_dev else None,
            exec_dev.id if exec_dev else None
        ]
    })
    
    return completion
```

---

### Deviation Dashboarding

```python
# Repository query for deviation summary

def get_deviation_summary_for_fermentation(fermentation_id: int) -> dict:
    """
    Dashboard widget: Current fermentation's deviations.
    """
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    
    timing_devs = TimingDeviation.filter(execution_id=execution.id)
    skip_devs = SkipDeviation.filter(execution_id=execution.id)
    exec_devs = ExecutionDeviation.filter(execution_id=execution.id)
    
    return {
        "total_deviations": len(timing_devs) + len(skip_devs) + len(exec_devs),
        "by_severity": {
            "CRITICAL": count(severity=CRITICAL),
            "HIGH": count(severity=HIGH),
            "MEDIUM": count(severity=MEDIUM),
            "LOW": count(severity=LOW)
        },
        "unacknowledged": count(acknowledged_at=None),
        "recent_deviations": [
            {
                "type": "TIMING",
                "step": step.description,
                "severity": "HIGH",
                "days_late": 1,
                "created_at": "2026-02-09T14:30:00Z"
            }
        ]
    }
```

---

### API Endpoints

```python
# GET /api/fermentations/{id}/protocol-deviations
# Returns all deviations with ability to acknowledge

@router.get("/fermentations/{fermentation_id}/protocol-deviations")
def get_deviations(fermentation_id: int):
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    return {
        "timing_deviations": serialize(TimingDeviation.filter(execution_id=execution.id)),
        "skip_deviations": serialize(SkipDeviation.filter(execution_id=execution.id)),
        "execution_deviations": serialize(ExecutionDeviation.filter(execution_id=execution.id))
    }

@router.post("/protocol-deviations/{deviation_id}/acknowledge")
def acknowledge_deviation(deviation_id: int, acknowledgment: str):
    deviation = TimingDeviation.get(id=deviation_id)
    deviation.acknowledged_at = datetime.now()
    deviation.winemaker_acknowledgment = acknowledgment
    deviation.save()
    return deviation
```

---

### Schema

```sql
CREATE TABLE timing_deviations (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    type VARCHAR(20),  -- EARLY, LATE
    expected_date TIMESTAMP,
    actual_date TIMESTAMP,
    days_variance INTEGER,
    severity VARCHAR(20),  -- LOW, MEDIUM, HIGH, CRITICAL
    reason_code VARCHAR(50),
    description TEXT,
    winemaker_acknowledgment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES protocol_executions(id),
    FOREIGN KEY (step_id) REFERENCES protocol_steps(id)
);

CREATE TABLE skip_deviations (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    skip_reason VARCHAR(50),
    severity VARCHAR(20),
    description TEXT,
    skip_notes TEXT,
    requires_investigation BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES protocol_executions(id),
    FOREIGN KEY (step_id) REFERENCES protocol_steps(id)
);

CREATE TABLE execution_deviations (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    type VARCHAR(50),  -- MISSING_DATA, PATTERN_ANOMALY
    severity VARCHAR(20),
    description TEXT,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES protocol_executions(id),
    FOREIGN KEY (step_id) REFERENCES protocol_steps(id)
);

CREATE INDEX idx_timing_dev_execution ON timing_deviations(execution_id);
CREATE INDEX idx_timing_dev_severity ON timing_deviations(severity);
CREATE INDEX idx_skip_dev_execution ON skip_deviations(execution_id);
CREATE INDEX idx_exec_dev_execution ON execution_deviations(execution_id);
```

---

## Consequences

### Positive ✅
- **Early detection**: Problems surface immediately, not at end
- **Winemaker-aware**: Can acknowledge and explain deviations
- **Audit trail**: Every deviation recorded with context
- **Integration ready**: Deviations feed into Analysis confidence
- **Severity-based**: Critical issues get alerting, minor ones don't

### Negative ⚠️
- **Alert fatigue**: Too many notifications could desensitize
  - Mitigated: Only CRITICAL timing devs alert immediately
  - MEDIUM/HIGH logged but shown in dashboard

---

## Testing Strategy

```python
def test_timing_deviation_late_critical():
    """Critical step 3 days late → CRITICAL severity"""
    step = ProtocolStep(is_critical=True, tolerance_hours=6, expected_day=3)
    completion = StepCompletion(
        completed_at=execution.start_date + timedelta(days=6)  # 3 days late
    )
    
    dev = detect_timing_deviation(step, completion)
    assert dev.severity == DeviationSeverity.CRITICAL
    assert dev.days_variance == 3

def test_timing_deviation_early_minor():
    """Early by 6 hours is acceptable, no deviation"""
    step = ProtocolStep(tolerance_hours=12, expected_day=5)
    completion = StepCompletion(
        completed_at=execution.start_date + timedelta(days=5, hours=-6)
    )
    
    dev = detect_timing_deviation(step, completion)
    assert dev is None

def test_skip_justified():
    """Justified skip → no deviation"""
    completion = StepCompletion(
        was_skipped=True,
        skip_reason=SkipReason.CONDITION_NOT_MET
    )
    
    dev = detect_skip_deviation(step, completion)
    assert dev is None

def test_skip_unjustified():
    """Unjustified skip on critical step → CRITICAL deviation"""
    step = ProtocolStep(is_critical=True)
    completion = StepCompletion(
        was_skipped=True,
        skip_reason=SkipReason.EQUIPMENT_FAILURE
    )
    
    dev = detect_skip_deviation(step, completion)
    assert dev.severity == DeviationSeverity.CRITICAL
```

---

## Questions for Susana

- [ ] Should timing tolerance be day-based (±3 days) or hour-based (±72 hours)?
- [ ] How many deviations trigger automatic escalation to head winemaker?
- [ ] Should we archive resolved deviations or keep full history?

