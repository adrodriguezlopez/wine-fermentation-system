# 🎯 ADR Implementation Priority - Dependency Map

**Status**: All 6 ADRs created, now determine execution order  
**Date**: February 9, 2026  
**Timeline**: 10 weeks to May 2026 demo

---

## 📊 Dependency Graph

```
ADR-035 (Data Model) ← FOUNDATIONAL
   ↓
   ├─→ ADR-036 (Compliance Scoring)
   ├─→ ADR-038 (Deviation Detection)
   ├─→ ADR-039 (Template Management)
   └─→ ADR-040 (Notifications & Alerts)
       ├─ depends on ADR-038 (deviation detection)
       └─ depends on ADR-036 (scoring for alert triggers)

ADR-037 (Analysis Integration)
   ├─ depends on ADR-035 (data model)
   ├─ depends on ADR-036 (confidence boosting uses scoring)
   └─ can go in parallel with 036/038
```

---

## 🚀 Implementation Order (What to Code First)

### PHASE 0: Foundation (Week 1-2) - DO THIS FIRST
**Goal**: Database schema + domain models ready

#### 1. **ADR-035: Protocol Data Model & Schema** ← START HERE
- **What**: Create 4 domain entities + 3 enums + database tables
- **Blocking**: Everything else depends on this
- **Effort**: 1-2 weeks
- **Deliverables**:
  - [ ] 4 Python domain entities (Protocol, Step, Execution, Completion)
  - [ ] 3 Enum classes (StepType, Status, SkipReason)
  - [ ] Database migration (4 tables, 6 indexes)
  - [ ] Seed script (load JSON protocols into database)
  - [ ] 100+ unit tests (relationships, constraints, validations)

**Work Items**:
```
Week 1 (Feb 9-15):
├─ Mon-Tue: Create domain entities (4 files, ~200 lines)
├─ Tue: Create enums (3 files, ~80 lines)
├─ Wed: Create repositories (4 files, CRUD + custom queries)
└─ Thu-Fri: Database migration + seed script

Week 2 (Feb 16-22):
├─ Mon: Run migration, verify schema
├─ Tue-Wed: Create integration tests
├─ Thu: Load seed data (Pinot/Chardonnay/Cabernet)
└─ Fri: Verify relationships work
```

**Why First**:
- Blocks all 5 other ADRs
- Your protocol data is ready (generated this week)
- Creates test data for future features
- Establishes database foundation

---

### PHASE 1: Core Services (Week 3-5) - PARALLEL TRACKS

#### 2a. **ADR-036: Compliance Scoring Algorithm** (CRITICAL)
- **What**: Calculate protocol compliance score (0-100%)
- **Dependencies**: ADR-035 (data model)
- **Effort**: 1-2 weeks
- **Deliverables**:
  - [ ] ProtocolComplianceService class
  - [ ] Scoring formula implementation
  - [ ] Varietal-specific weighting
  - [ ] Compliance trend tracking
  - [ ] Unit tests for scoring edge cases

**Formula**:
```
Compliance Score = (Steps Completed On-Time / Total Steps) × 100%

Weighted = Σ(completed_step.criticality_score) / Σ(all_step.criticality_score) × 100%

Adjustments:
- Late steps: -2% per day late (capped)
- Skipped critical steps: -15% each
- Skipped optional steps: -1% each
- Early completion: +5% (up to +10% for early protocols)
```

**Work Items**:
```
Week 3 (Feb 23-Mar 1):
├─ Mon: Implement basic scoring formula
├─ Tue: Add varietal-specific weights
├─ Wed: Create scoring service methods
├─ Thu-Fri: Write comprehensive tests
```

#### 2b. **ADR-038: Deviation Detection Strategy** (PARALLEL)
- **What**: Detect when protocol steps are late/skipped/failed
- **Dependencies**: ADR-035 (data model)
- **Effort**: 1 week
- **Deliverables**:
  - [ ] DeviationDetector service
  - [ ] Late-step detection (compares expected_day vs actual)
  - [ ] Varietal-specific tolerance windows
  - [ ] Deviation scoring
  - [ ] Unit + integration tests

**Deviations Tracked**:
```
TIMING_DEVIATION: Step completed >tolerance_hours late
  - Pinot H2S Check: >6 hours late = CRITICAL
  - Cabernet Punch: >12 hours late = MEDIUM

SKIP_DEVIATION: Step marked as skipped
  - Critical skip = CRITICAL deviation
  - Optional skip = LOW deviation

CONDITION_DEVIATION: Step conditions not met
  - "Brix should be 16-18" = track if 20+ or 12-
  - "Temperature 18-22°C" = track if outside

QUALITY_DEVIATION: Observations indicate problem
  - "H2S smell detected" = quality deviation
  - "Stuck fermentation" = quality deviation
```

**Work Items**:
```
Week 4 (Mar 2-8):
├─ Mon-Tue: Implement deviation detection logic
├─ Wed: Add varietal-specific thresholds
├─ Thu: Write tests
└─ Fri: Integration with ADR-036
```

#### 2c. **ADR-039: Template Management** (PARALLEL)
- **What**: Manage protocol templates, versions, customization
- **Dependencies**: ADR-035 (data model)
- **Effort**: 1 week
- **Deliverables**:
  - [ ] ProtocolTemplateService class
  - [ ] Version management (v1.0 → v2.0)
  - [ ] Template activation/deactivation
  - [ ] Custom step injection
  - [ ] Tests

**Work Items**:
```
Week 3-4:
├─ Create ProtocolTemplateService
├─ Implement version lifecycle
├─ Add step customization
└─ Test with seed protocols
```

---

### PHASE 2: Integration (Week 5-7)

#### 3. **ADR-037: Protocol-Analysis Integration** (HIGH PRIORITY)
- **What**: Connect Protocol Engine ↔ Analysis Engine
- **Dependencies**: ADR-035 (data model), ADR-036 (scoring)
- **Effort**: 2 weeks
- **Deliverables**:
  - [ ] Bidirectional protocol ↔ analysis event system
  - [ ] Confidence boosting based on protocol compliance
  - [ ] Anomaly flagging based on protocol deviations
  - [ ] Test integration with existing Analysis Engine

**Integration Points**:
```
Protocol → Analysis:
  "Fermentation is 3 days late on H2S check"
  → Analysis Engine should: LOWER confidence in H2S readings
  
Analysis → Protocol:
  "Detected H2S spike"
  → Protocol Engine should: FLAG H2S deviation, suggest urgent check
```

**Work Items**:
```
Week 5-6:
├─ Define event contracts
├─ Implement event publishing
├─ Create confidence adjustment logic
├─ Write integration tests
```

---

### PHASE 3: User Notifications (Week 7-9)

#### 4. **ADR-040: Notifications & Alerts** (MEDIUM PRIORITY)
- **What**: Real-time alerts when deviations detected
- **Dependencies**: ADR-035, ADR-036, ADR-038 (all prior)
- **Effort**: 2-3 weeks
- **Deliverables**:
  - [ ] NotificationService (send alerts)
  - [ ] Alert triggers (late steps, skipped steps, quality issues)
  - [ ] Severity levels (CRITICAL, HIGH, MEDIUM, LOW)
  - [ ] Offline-first cache (mobile app can work offline)
  - [ ] Email/SMS/push notification handlers

**Alert Examples**:
```
CRITICAL: "Pinot Noir H2S check >6h late - check for spoilage"
HIGH: "Chardonnay DAP addition window closing (4h left)"
MEDIUM: "Cabernet pressing scheduled for tomorrow - prepare equipment"
LOW: "Optional MLF inoculation: ready when you are"
```

**Work Items**:
```
Week 7-9:
├─ Create NotificationService
├─ Define alert triggers
├─ Implement severity calculation
├─ Build offline cache
└─ Write tests
```

---

## 📅 Week-by-Week Roadmap

```
WEEK 1-2: ADR-035 (FOUNDATIONAL)
├─ Feb 9-15:  Domain entities + enums + repositories
├─ Feb 16-22: Database migration + seed script
└─ Result: Database live with 3 seed protocols

WEEK 3-5: PARALLEL (ADR-036, 038, 039)
├─ Feb 23-Mar 1:  Compliance scoring (ADR-036)
├─ Mar 2-8:       Deviation detection (ADR-038)
├─ Mar 2-8:       Template management (ADR-039)
└─ Result: Core services working independently

WEEK 5-7: ADR-037 (INTEGRATION)
├─ Mar 9-15: Protocol ↔ Analysis bidirectional events
├─ Mar 16-22: Confidence adjustment + testing
└─ Result: Protocols talk to Analysis Engine

WEEK 7-9: ADR-040 (NOTIFICATIONS)
├─ Mar 23-29: Alert triggers + notification service
├─ Mar 30-Apr 5: Offline-first implementation
└─ Result: Users get real-time alerts

WEEK 10: BUFFER & TESTING
├─ Apr 6-12: Integration testing
├─ Apr 13-19: Load testing + performance optimization
└─ Result: Ready for May demo
```

---

## 🎯 Critical Path (MUST DO IN ORDER)

```
ADR-035 (Week 1-2) ✅ Start immediately
    ↓
ADR-036 (Week 3-4) ← Blocks ADR-040
    ↓
ADR-038 (Week 4-5) ← Blocks ADR-040
    ↓
ADR-040 (Week 7-9) ← Final piece
```

**Non-Critical Path** (can do in parallel):
- ADR-037 (week 5-7, doesn't block anything)
- ADR-039 (week 3-4, nice-to-have early)

---

## ✅ Why This Order?

### ADR-035 First (MANDATORY)
- Everything else depends on database schema
- Need entities before writing services
- Seed data ready (generated this week)
- Creates test fixtures for all other ADRs

### ADR-036 + 038 Together (CRITICAL PATH)
- Both use same data (ProtocolExecution, StepCompletion)
- Scoring + deviation detection are tightly coupled
- Both needed for alert triggers (ADR-040)
- Can test independently

### ADR-039 Early (NICE-TO-HAVE)
- Template management not on critical path
- Can be added later without breaking flow
- But useful for handling multiple winery templates
- Good to do in parallel with scoring/deviations

### ADR-037 Middle (INTEGRATION)
- Depends on ADR-036 (uses compliance scores)
- Non-blocking (Protocol Engine works without Analysis)
- Can be deferred to Week 6-7 if needed
- Boosts Analysis Engine accuracy

### ADR-040 Last (NOTIFICATIONS)
- Depends on all prior services
- Needs triggers (ADR-038), scoring (ADR-036), etc.
- Least critical for May demo
- Could be "phase 2" feature (July)

---

## 🚀 START THIS WEEK

### Monday (Today):
```
ADR-035 Implementation Kickoff
├─ Create src/modules/fermentation/src/domain/entities/
├─ Create 4 entity files:
│  ├─ protocol_protocol.py
│  ├─ protocol_step.py
│  ├─ protocol_execution.py
│  └─ step_completion.py
├─ Create src/modules/fermentation/src/domain/enums/
│  ├─ step_type.py
│  ├─ protocol_execution_status.py
│  └─ skip_reason.py
└─ Commit to git
```

### Wednesday:
```
ADR-035 - Repositories
├─ Create 4 repository interfaces
├─ Create 4 repository implementations
├─ Wire into dependency injection
└─ Write 50+ unit tests
```

### Friday:
```
ADR-035 - Database
├─ Create migration script
├─ Run migration locally
├─ Create seed loader
├─ Load protocols: Pinot/Chardonnay/Cabernet
├─ Verify relationships work
└─ Commit & ready for Phase 1
```

---

## 📊 Dependencies at a Glance

```
┌─────────────────────────────────────────┐
│ ADR-035: Data Model (FOUNDATION)        │
│ - 4 entities, 3 enums, 4 repositories   │
│ - Database schema + seed data           │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────────┬──────────┬──────────┐
    │                 │          │          │
    ▼                 ▼          ▼          ▼
┌─────────┐      ┌──────┐  ┌──────────┐  ┌──────────┐
│ADR-036  │      │ADR-38│  │ ADR-037  │  │ ADR-039  │
│Scoring  │      │Devitn│  │Analysis  │  │Template  │
└────┬────┘      └──┬───┘  └────┬─────┘  └──────────┘
     │              │           │
     └──────┬───────┘           │
            │                   │
            ▼                   │
       ┌──────────┐             │
       │ ADR-040  │◄────────────┘
       │ Alerts   │
       └──────────┘
```

---

## ✨ Summary

**Start**: ADR-035 (Data Model) - begins Monday  
**Week 2**: ADR-035 complete, database live  
**Week 3-5**: ADR-036, 038, 039 in parallel  
**Week 5-7**: ADR-037 integration  
**Week 7-9**: ADR-040 notifications  
**Week 10**: Final testing + May demo prep  

**Key Win**: Generated protocol data (Pinot/Chardonnay/Cabernet) is READY NOW - no waiting for manual extraction. Start building infrastructure immediately. 🍷

