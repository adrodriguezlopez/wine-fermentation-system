# ADR-037: Protocol-Analysis Engine Integration

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team  
**Related ADRs**: ADR-021 (Protocol Engine), ADR-020 (Analysis Engine), ADR-036 (Compliance Scoring)  
**Timeline Context**: Phase 3 integration (Week 6-7)

---

## Context and Problem Statement

The **Protocol Compliance Engine** and **Analysis Engine** must work together:

1. **Protocol Compliance Score** → Input to Analysis confidence calculation
   - "If protocol compliance is 92%, we're more confident in density predictions"
   - "If protocol compliance is 50%, anomalies might be due to protocol deviation"

2. **Analysis Output** → Informs protocol adjustments
   - Anomaly detected early → Protocol step accelerated
   - Stuck fermentation → Analysis suggests skip H2S check step

3. **Joint Context** → More accurate predictions
   - Same fermentation tracked by two systems
   - Each system makes decisions based on other's state

---

## Decision

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Fermentation (Domain Core)                              │
│ - batch_name, varietal, start_date, temperature, etc.   │
└────────────────┬─────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    ┌────▼──────────┐   ┌────▼──────────────┐
    │ Protocol      │   │ Analysis          │
    │ Execution     │   │ (Fermentation)    │
    │               │   │                   │
    │ • Steps       │   │ • Samples         │
    │ • Compliance  │   │ • Anomalies       │
    │   Score: 87%  │   │ • Trend           │
    └────┬──────────┘   │                   │
         │              │ Confidence:       │
         │              │ - Base: 0.75      │
         │              │ + Protocol: 0.12  │
         │              │ ────────────────  │
         │              │ Final: 0.87       │
         └──────────────┤                   │
                  Uses  └───────────────────┘
```

### Data Exchange Points

#### 1. **Protocol Score → Analysis Confidence Boost** (Real-time)

When Analysis Engine calculates confidence in anomaly detection:

```python
def calculate_anomaly_confidence(
    analysis: Analysis,
    fermentation_id: int
) -> dict:
    """
    Adjust confidence based on protocol compliance.
    """
    # Base confidence from sample data quality
    base_confidence = calculate_trend_confidence(
        samples=analysis.samples,
        trend_days=7
    )  # Returns 0.0 - 1.0
    
    # Get protocol compliance score
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    protocol_compliance_pct = execution.compliance_score / 100.0
    
    # Protocol compliance multiplier
    # Range: 0.5 (low compliance, low confidence) to 1.5 (high compliance, high confidence)
    compliance_multiplier = 0.5 + (protocol_compliance_pct * 1.0)
    
    # Adjusted confidence
    adjusted_confidence = base_confidence * compliance_multiplier
    adjusted_confidence = min(adjusted_confidence, 1.0)  # Cap at 100%
    
    return {
        "base_confidence": round(base_confidence, 3),
        "protocol_compliance_score": protocol_compliance_pct,
        "compliance_multiplier": round(compliance_multiplier, 3),
        "adjusted_confidence": round(adjusted_confidence, 3),
        "confidence_boost_pct": round(
            (adjusted_confidence - base_confidence) * 100, 
            1
        )
    }


# Example:
# - Base: 0.75 (good data, 7-day trend)
# - Protocol: 87% → multiplier = 0.5 + (0.87 × 1.0) = 1.37
# - Final: 0.75 × 1.37 = 1.03 → capped at 1.0
# - Result: "Confidence boosted from 75% to 100%"

# Counter-example:
# - Base: 0.75
# - Protocol: 45% (poor compliance) → multiplier = 0.5 + (0.45 × 1.0) = 0.95
# - Final: 0.75 × 0.95 = 0.71
# - Result: "Confidence reduced from 75% to 71% due to low protocol compliance"
```

#### 2. **Analysis Output → Protocol Advisory** (Batch, End-of-Day)

When Analysis Engine detects anomalies, suggest protocol adjustments:

```python
def suggest_protocol_adjustments(
    analysis: Analysis,
    execution: ProtocolExecution
) -> Optional[ProtocolAdvisory]:
    """
    Suggest which protocol steps should be accelerated/skipped based on anomalies.
    
    Returns advisory if pattern detected, None otherwise.
    """
    
    recommendations = analysis.recommendations  # From Analysis Engine
    
    # Pattern 1: Volatile temperature
    if any(r.category == "TEMPERATURE_VOLATILITY" for r in recommendations):
        return ProtocolAdvisory(
            execution_id=execution.id,
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type=StepType.TEMPERATURE_CHECK,
            suggestion="Temperature volatile - increase monitoring frequency",
            confidence=0.85,
            risk_level=RiskLevel.MEDIUM
        )
    
    # Pattern 2: Stuck fermentation (Brix not dropping)
    if any(r.category == "FERMENTATION_STALLED" for r in recommendations):
        stuck_day = analysis.stall_detected_day  # From Analysis
        protocol_steps = execution.protocol.steps
        
        # Find next nutrient/DAP step
        next_nutrient_step = next(
            (s for s in protocol_steps if s.step_order > stuck_day
             and s.step_type in [StepType.DAP_ADDITION, StepType.NUTRIENT_ADDITION]),
            None
        )
        
        if next_nutrient_step:
            return ProtocolAdvisory(
                execution_id=execution.id,
                advisory_type=AdvisoryType.ACCELERATE_STEP,
                target_step_type=next_nutrient_step.step_type,
                suggestion=f"Fermentation stalled - consider accelerating {next_nutrient_step.description}",
                confidence=0.92,
                risk_level=RiskLevel.HIGH
            )
    
    # Pattern 3: H2S smell detected (Anomaly)
    if any(r.category == "H2S_DETECTED" for r in recommendations):
        return ProtocolAdvisory(
            execution_id=execution.id,
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type=StepType.H2S_CHECK,
            suggestion="H2S detected - add aeration/punch-down immediately",
            confidence=0.95,
            risk_level=RiskLevel.CRITICAL
        )
    
    # Pattern 4: Completed fermentation early
    if any(r.category == "FERMENTATION_COMPLETE" for r in recommendations):
        next_step = next(
            (s for s in execution.protocol.steps if not execution.is_step_completed(s.id)),
            None
        )
        
        if next_step:
            return ProtocolAdvisory(
                execution_id=execution.id,
                advisory_type=AdvisoryType.SKIP_STEP,
                target_step_type=next_step.step_type,
                suggestion=f"Fermentation complete - {next_step.description} not needed",
                confidence=0.88,
                risk_level=RiskLevel.LOW
            )
    
    return None


# Store advisory (shown in UI, audit trail)
advisory = suggest_protocol_adjustments(analysis, execution)
if advisory:
    advisory.save()
    # Log event: "Analysis suggests accelerate H2S_CHECK"
```

#### 3. **Protocol Changes → Analysis Recalibration** (Batch)

When protocol execution changes (step skipped, accelerated, etc.):

```python
def recalibrate_analysis_on_protocol_change(
    fermentation_id: int,
    change_type: str  # "STEP_SKIPPED", "STEP_ACCELERATED", "EXECUTION_PAUSED"
) -> None:
    """
    Recalibrate analysis models after protocol changes.
    Called via event listener when ProtocolExecution updates.
    """
    
    analysis = Analysis.get(fermentation_id=fermentation_id)
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    
    # Recalculate baseline expectations
    if change_type == "STEP_SKIPPED":
        # Removed a nutrient step? Expect slower fermentation
        analysis.recalibrate_expected_trajectory()
    
    elif change_type == "STEP_ACCELERATED":
        # Added aeration early? Might speed up fermentation
        analysis.recalibrate_expected_trajectory()
    
    elif change_type == "EXECUTION_PAUSED":
        # Fermentation paused? Recalibrate duration estimates
        analysis.expected_completion_date = None
    
    analysis.save()
    
    # Log: "Analysis recalibrated after protocol change"
```

---

### Schema Extension

Add linking table:

```sql
-- If not using direct foreign keys, maintain event log
CREATE TABLE protocol_analysis_events (
    id SERIAL PRIMARY KEY,
    fermentation_id INTEGER NOT NULL,
    event_type VARCHAR(50),  -- "COMPLIANCE_UPDATED", "ANOMALY_DETECTED", "ADVISORY_GENERATED"
    source_system VARCHAR(20),  -- "PROTOCOL" or "ANALYSIS"
    source_id INTEGER,  -- Which step/anomaly triggered this?
    payload JSON,  -- Event details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fermentation_id) REFERENCES fermentations(id)
);

CREATE INDEX idx_protocol_analysis_events_fermentation ON protocol_analysis_events(fermentation_id);
```

### API Contracts

#### Protocol → Analysis (Read-Only)
```json
// GET /api/fermentations/{id}/protocol-status
{
  "fermentation_id": 123,
  "protocol_id": 456,
  "compliance_score": 87.5,
  "completed_steps": 12,
  "pending_steps": 8,
  "skipped_critical_steps": 0,
  "status": "ACTIVE"
}
```

#### Analysis → Protocol (Advisory Channel)
```json
// POST /api/fermentations/{id}/protocol-advisories
{
  "fermentation_id": 123,
  "advisory_type": "ACCELERATE_STEP",
  "target_step_type": "H2S_CHECK",
  "suggestion": "H2S detected - add aeration",
  "confidence": 0.95,
  "risk_level": "CRITICAL",
  "recommended_action": "NEXT 2 HOURS"
}
```

---

## Implementation Roadmap

### Phase 1: Data Structure (Week 6)
- [ ] Create `protocol_analysis_events` table
- [ ] Add protocol_id foreign key to Analysis (optional, for traceability)
- [ ] Update ProtocolExecution to expose compliance_score via API

### Phase 2: Confidence Boost (Week 6)
- [ ] Implement `calculate_anomaly_confidence()` function
- [ ] Update Anomaly.confidence = base × compliance_multiplier
- [ ] Unit tests: confidence changes with compliance

### Phase 3: Advisories (Week 7)
- [ ] Implement `suggest_protocol_adjustments()` function
- [ ] Add ProtocolAdvisory entity + repository
- [ ] Create advisory generation workflow
- [ ] Unit tests: correct advisories for known patterns

### Phase 4: Recalibration (Week 7)
- [ ] Add event listener for ProtocolExecution changes
- [ ] Implement `recalibrate_analysis_on_protocol_change()`
- [ ] Integration tests: changes propagate correctly

### Phase 5: UI Integration (Week 8)
- [ ] Display compliance score in fermentation dashboard
- [ ] Show advisories to winemaker
- [ ] Allow winemaker to acknowledge/dismiss advisories
- [ ] Audit trail of all advisory actions

---

## Consequences

### Positive ✅
- **Context-aware analysis**: Confidence scales with execution quality
- **Bi-directional communication**: Systems inform each other
- **Better predictions**: Protocol compliance → more accurate anomaly detection
- **Proactive suggestions**: Analysis → suggests protocol adjustments
- **Audit trail**: All cross-system events logged

### Negative ⚠️
- **Circular dependencies**: Need careful event handling (mitigated by event log)
- **Complexity**: Two systems must stay in sync
- **Testing overhead**: Need integration tests for both directions

---

## Error Handling

```python
# What if protocol_execution doesn't exist?
try:
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
except ProtocolExecution.DoesNotExist:
    # Protocol not assigned yet - use default confidence
    adjusted_confidence = base_confidence  # No boost/penalty
    logger.info(f"No protocol assigned to fermentation {fermentation_id}")

# What if recalibration fails?
try:
    recalibrate_analysis_on_protocol_change(fermentation_id, change_type)
except Exception as e:
    # Log error but don't fail protocol update
    logger.error(f"Recalibration failed: {e}")
    # Analysis continues with old calibration until next sync
```

---

## Testing Strategy

```python
# test_protocol_analysis_integration.py

def test_high_compliance_boosts_confidence():
    """87% protocol compliance → confidence multiplier 1.37"""
    execution.compliance_score = 87
    result = calculate_anomaly_confidence(analysis, fermentation_id)
    assert result["compliance_multiplier"] == pytest.approx(1.37, 0.01)

def test_low_compliance_reduces_confidence():
    """45% protocol compliance → confidence multiplier 0.95"""
    execution.compliance_score = 45
    result = calculate_anomaly_confidence(analysis, fermentation_id)
    assert result["compliance_multiplier"] == pytest.approx(0.95, 0.01)

def test_stuck_fermentation_suggests_nutrient_step():
    """Stalled fermentation → suggest accelerate DAP_ADDITION"""
    analysis.recommendations = [Recommendation(category="FERMENTATION_STALLED")]
    advisory = suggest_protocol_adjustments(analysis, execution)
    assert advisory.target_step_type == StepType.DAP_ADDITION

def test_h2s_detected_suggests_h2s_check():
    """H2S anomaly → suggest accelerate H2S_CHECK"""
    analysis.recommendations = [Recommendation(category="H2S_DETECTED")]
    advisory = suggest_protocol_adjustments(analysis, execution)
    assert advisory.target_step_type == StepType.H2S_CHECK

def test_protocol_change_triggers_recalibration():
    """Protocol step skipped → analysis recalibrated"""
    with patch.object(Analysis, 'recalibrate_expected_trajectory') as mock:
        recalibrate_analysis_on_protocol_change(fermentation_id, "STEP_SKIPPED")
        mock.assert_called_once()
```

---

## Questions for Susana

- [ ] Should protocol advisories require winemaker confirmation before acting?
- [ ] What's the acceptable delay between protocol change and analysis recalibration?
- [ ] Should very high-confidence advisories (95%+) auto-alert via SMS/email?

