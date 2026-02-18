# ADR-036: Protocol Compliance Scoring Algorithm

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team + Enologist  
**Related ADRs**: ADR-035 (Data Model), ADR-021 (Protocol Engine), ADR-023 (Analysis Integration)  
**Timeline Context**: Phase 2 implementation (Week 4-5)

---

## Context and Problem Statement

From **AI Enologist Analysis**, we know compliance scoring should:
- **Weight by criticality**: H2S checks ≠ visual inspections
- **Penalize lateness**: Off-schedule steps matter
- **Allow justified skips**: Not all skips = non-compliance
- **Support varietal differences**: Pinot Noir stricter than Cabernet for timing
- **Enable winemaker override**: Trust the expert judgment

The scoring must:
1. Be **deterministic** (same inputs → same score)
2. Be **explainable** (winemaker can understand why 87% not 88%)
3. Be **actionable** (highlight which steps are dragging score down)
4. Be **real-time** (calculate as steps complete, not just at end)

---

## Decision

### Compliance Score Formula

```
COMPLIANCE_SCORE = (WEIGHTED_COMPLETION_SCORE × 0.7) + (TIMING_SCORE × 0.3)

Where:
- WEIGHTED_COMPLETION_SCORE = (Sum of: Step_Completion_Points) / Total_Possible_Points
- TIMING_SCORE = (On_Time_Steps / Total_Completed_Steps) × 100
```

#### Step 1: Calculate Weighted Completion Score

For each step in the protocol:

```python
def calculate_step_completion_points(step: ProtocolStep, completion: Optional[StepCompletion]) -> dict:
    """
    Determine points earned for a single step.
    
    Returns:
        {
            "earned_points": float,      # What this completion achieved
            "possible_points": float,    # Max points for this step
            "step_id": int,
            "step_type": StepType,
            "notes": str                 # Why these points?
        }
    """
    
    # Step 1a: Determine maximum points based on criticality
    base_points = 100  # Start with 100 max per step
    criticality_multiplier = step.criticality_score / 100.0  # 0.5 to 2.0
    possible_points = base_points * criticality_multiplier
    
    # Step 1b: Did not complete = 0 points
    if completion is None:
        return {
            "earned_points": 0,
            "possible_points": possible_points,
            "step_id": step.id,
            "step_type": step.step_type,
            "notes": "Step not completed"
        }
    
    # Step 1c: Skip analysis
    if completion.was_skipped:
        skip_reason = completion.skip_reason
        
        # Justified skips: earn partial credit (60% of points)
        justified_skips = [
            SkipReason.CONDITION_NOT_MET,  # e.g., "pH already optimal"
            SkipReason.FERMENTATION_ENDED,  # e.g., "Brix now negative"
            SkipReason.WINEMAKER_DECISION,  # Expert judgment
        ]
        
        if skip_reason in justified_skips:
            earned = possible_points * 0.60
            return {
                "earned_points": earned,
                "possible_points": possible_points,
                "step_id": step.id,
                "step_type": step.step_type,
                "notes": f"Justifiably skipped ({skip_reason.value}): 60% credit"
            }
        
        # Unjustified skips: 0 points
        else:
            return {
                "earned_points": 0,
                "possible_points": possible_points,
                "step_id": step.id,
                "step_type": step.step_type,
                "notes": f"Skipped without justification ({skip_reason.value})"
            }
    
    # Step 1d: Step completed - start with 100% of possible points
    earned_points = possible_points
    
    # Step 1e: Timing penalty
    if completion.is_on_schedule:
        # Completed within tolerance window: no penalty
        timing_penalty = 0
    else:
        # Late completion: penalize based on days_late
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
    earned_points = max(earned_points, 0)  # Never go below 0
    
    return {
        "earned_points": earned_points,
        "possible_points": possible_points,
        "step_id": step.id,
        "step_type": step.step_type,
        "notes": f"On-time: {completion.is_on_schedule}; Days late: {completion.days_late}"
    }


def calculate_weighted_completion_score(
    protocol: FermentationProtocol,
    execution: ProtocolExecution
) -> dict:
    """
    Calculate overall weighted completion score (0-100).
    
    Returns:
        {
            "score": float,              # 0-100
            "step_breakdown": [dict],    # Per-step details
            "total_earned": float,
            "total_possible": float,
            "completed_count": int,
            "skipped_count": int,
            "pending_count": int
        }
    """
    step_results = []
    total_earned = 0
    total_possible = 0
    completed_count = 0
    skipped_count = 0
    
    for step in protocol.steps:  # Ordered by step_order
        completion = execution.get_completion_for_step(step.id)  # None if not done
        result = calculate_step_completion_points(step, completion)
        
        step_results.append(result)
        total_earned += result["earned_points"]
        total_possible += result["possible_points"]
        
        if completion:
            if completion.was_skipped:
                skipped_count += 1
            else:
                completed_count += 1
    
    pending_count = len(protocol.steps) - completed_count - skipped_count
    
    # Avoid division by zero
    if total_possible == 0:
        score = 0
    else:
        score = (total_earned / total_possible) * 100
    
    return {
        "score": round(score, 2),
        "step_breakdown": step_results,
        "total_earned": round(total_earned, 2),
        "total_possible": round(total_possible, 2),
        "completed_count": completed_count,
        "skipped_count": skipped_count,
        "pending_count": pending_count
    }
```

#### Step 2: Calculate Timing Score

```python
def calculate_timing_score(execution: ProtocolExecution) -> dict:
    """
    Percentage of completed steps that were on-time.
    """
    completions = execution.completions.filter(was_skipped=False)
    
    if not completions:
        return {
            "score": 100,  # No completed steps = no timing issues yet
            "on_time_count": 0,
            "late_count": 0,
            "total_completed": 0
        }
    
    on_time_count = sum(1 for c in completions if c.is_on_schedule)
    late_count = len(completions) - on_time_count
    
    score = (on_time_count / len(completions)) * 100 if completions else 0
    
    return {
        "score": round(score, 2),
        "on_time_count": on_time_count,
        "late_count": late_count,
        "total_completed": len(completions)
    }
```

#### Step 3: Combine Into Final Score

```python
def calculate_compliance_score(execution: ProtocolExecution) -> dict:
    """
    Final compliance score combining weighted completion and timing.
    """
    protocol = execution.protocol
    
    completion_score_data = calculate_weighted_completion_score(protocol, execution)
    timing_score_data = calculate_timing_score(execution)
    
    # Final formula: 70% completion, 30% timing
    final_score = (
        (completion_score_data["score"] * 0.70) +
        (timing_score_data["score"] * 0.30)
    )
    
    # Boost if all required (critical) steps done
    critical_steps = [s for s in protocol.steps if s.is_critical]
    completed_critical = sum(
        1 for step in critical_steps
        if any(c.step_id == step.id and not c.was_skipped 
               for c in execution.completions)
    )
    
    critical_completion_pct = (
        (completed_critical / len(critical_steps) * 100) 
        if critical_steps else 100
    )
    
    # If all critical steps done: +5 bonus (max 105 before capping)
    if critical_completion_pct == 100:
        final_score = min(final_score + 5, 100)
    elif critical_completion_pct < 100:
        # If any critical step missing: -15 penalty
        final_score = max(final_score - 15, 0)
    
    return {
        "compliance_score": round(min(final_score, 100), 2),
        "weighted_completion": round(completion_score_data["score"], 2),
        "timing_score": round(timing_score_data["score"], 2),
        "critical_steps_completion_pct": round(critical_completion_pct, 2),
        "breakdown": {
            "completion": completion_score_data,
            "timing": timing_score_data
        }
    }
```

---

### Example Calculation

**Scenario: Cabernet Sauvignon, Day 12 of 28**

| Step | Type | Critical | Max Pts | Status | Earned | Notes |
|------|------|----------|---------|--------|--------|-------|
| 1 | Yeast Inoculation | Yes ✓ | 150 | ✓ On-time | 150 | Day 0, within window |
| 2 | H2S Check | Yes ✓ | 150 | ✓ Day 2 (1 day late) | 112 | -25% penalty (0.25 × 150) |
| 3 | DAP Addition | Yes ✓ | 150 | ✓ On-time | 150 | Day 3 |
| 4 | PUNCH_DOWN | No ✗ | 50 | ✓ On-time | 50 | |
| 5 | Temp Check | No ✗ | 50 | ✗ Skipped (FERMENTATION_ENDED) | 30 | 60% credit for justification |
| 6 | Racking | No ✗ | 50 | ⏳ Pending | 0 | Not yet |
| 7 | SO2 Addition | No ✗ | 50 | ⏳ Pending | 0 | Not yet |

**Calculations:**
- **Total Earned**: 150 + 112 + 150 + 50 + 30 + 0 + 0 = 492
- **Total Possible**: 150 + 150 + 150 + 50 + 50 + 50 + 50 = 650
- **Weighted Completion Score**: (492 / 650) × 100 = **75.69%**
- **Timing Score**: (5 on-time / 5 completed) × 100 = **100%** (skipped step doesn't count)
- **Final Score**: (75.69 × 0.70) + (100 × 0.30) = 52.98 + 30 = **82.98%**
- **Critical Step Check**: 3/3 critical steps done (with H2S one day late) = no penalty
- **Final**: **83%**

---

## Implementation Details

### Storage Strategy
```python
# Update ProtocolExecution when step completes
execution.compliance_score = calculate_compliance_score(execution)
execution.completed_steps = count(NOT skipped)
execution.skipped_critical_steps = count(critical AND skipped)
```

### Real-Time Updates
- Every `StepCompletion` triggers recalculation
- Score updates instantly in API responses
- Webhook triggers for Analysis Engine (ADR-023)

### Query Performance
```sql
-- Get current compliance score for all active fermentations
SELECT 
    pe.id,
    fe.batch_name,
    pe.compliance_score,
    pe.completed_steps,
    COUNT(CASE WHEN ps.is_critical THEN 1 END) as total_critical_steps
FROM protocol_executions pe
JOIN fermentations fe ON pe.fermentation_id = fe.id
JOIN fermentation_protocols fp ON pe.protocol_id = fp.id
LEFT JOIN protocol_steps ps ON fp.id = ps.protocol_id
WHERE pe.status = 'ACTIVE' AND pe.winery_id = $1
GROUP BY pe.id;
```

---

## Consequences

### Positive ✅
- **Transparent**: Winemaker can see exactly why score is X, not Y
- **Flexible**: Justified skips don't tank score
- **Weighted**: Critical steps matter more
- **Real-time**: Score updates as work progresses
- **Interpretable**: Matches human intuition (completion % + timing matter)

### Negative ⚠️
- **Complexity**: Formula not trivial (mitigated by good documentation)
- **Winemaker education needed**: Why is score 83% not 85%?

---

## Testing Strategy

```python
# test_compliance_scoring.py

def test_perfect_execution():
    """All steps on-time, no skips"""
    score = calculate_compliance_score(execution)
    assert score["compliance_score"] == 100
    assert score["critical_steps_completion_pct"] == 100

def test_one_critical_step_missing():
    """Missing one critical step = significant penalty"""
    score = calculate_compliance_score(execution_missing_h2s_check)
    assert score["compliance_score"] < 85  # -15% penalty

def test_justified_skip():
    """Justified skip earns 60% credit"""
    score = calculate_compliance_score(execution_justified_skip)
    assert score["breakdown"]["completion"]["step_breakdown"][4]["earned_points"] > 0

def test_late_by_one_day():
    """One day late = 25% penalty"""
    score = calculate_compliance_score(execution_one_day_late)
    # Should lose ~37 points (150 × 0.25)
    assert score["compliance_score"] < 85

def test_critical_vs_optional():
    """Critical steps worth more than optional"""
    critical_max = 150  # criticality_score 1.5
    optional_max = 50   # criticality_score 0.5
    assert critical_max > optional_max
```

---

## Questions for Validation

- [ ] Should skipped critical steps have different penalty than optional?
- [ ] Should very late steps (5+ days) have -100% vs cap at 0?
- [ ] Should incomplete protocols (fermentation ongoing) use different formula than final?

