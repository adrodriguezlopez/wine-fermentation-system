# Protocol Implementation ADRs - Comprehensive Guide

**Created**: February 9, 2026  
**For**: May 2026 Demo (10-week implementation)  
**Context**: Complete wine fermentation system with Protocol Compliance Engine

---

## 📋 New ADRs for Protocol Implementation (ADR-035 through ADR-040)

These ADRs define the complete Protocol Compliance Engine architecture, building on existing ADRs (ADR-021 established the vision, ADRs 025-027 provide multi-tenancy/logging infrastructure).

### Quick Navigation

| ADR | Title | Focus | Timeline | Priority |
|-----|-------|-------|----------|----------|
| [ADR-035](#adr-035-protocol-data-model--schema-design) | Data Model & Schema | Domain entities, DB schema | Week 1-2 | **CRITICAL** |
| [ADR-036](#adr-036-compliance-scoring-algorithm) | Compliance Scoring | Score calculation, weighting | Week 4-5 | **CRITICAL** |
| [ADR-037](#adr-037-protocol-analysis-integration) | Analysis Integration | Protocol ↔ Analysis bidirectional | Week 6-7 | **HIGH** |
| [ADR-038](#adr-038-deviation-detection) | Deviation Detection | Timing/skip/quality deviations | Week 5-6 | **HIGH** |
| [ADR-039](#adr-039-template-management) | Template Management | Admin templates → user instances | Week 3-4 | **HIGH** |
| [ADR-040](#adr-040-notifications--alerts) | Notifications & Alerts | Real-time alerts, offline-first | Week 7-9 | **MEDIUM** |

---

## 🏗️ ADR-035: Protocol Data Model & Schema Design

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 1-2  
**Dependencies**: None (foundational)

### What This Decides

The **domain model** for fermentation protocols:

1. **FermentationProtocol** - Master template (e.g., "Cabernet Sauvignon v2.0")
   - Varietal-specific, version-tracked
   - Contains ordered steps with criticality scoring

2. **ProtocolStep** - Single step in protocol (e.g., "Add DAP at 1/3 sugar depletion")
   - Day-based scheduling with tolerance windows (±N hours)
   - Can be repeated daily or one-time
   - Dependency tracking (must complete step X first)

3. **ProtocolExecution** - Per-fermentation tracking (e.g., "Batch 2026-CS-001 following Cabernet v2.0")
   - Links fermentation to protocol
   - Tracks compliance score (0-100%)
   - Status: NOT_STARTED → ACTIVE → COMPLETED

4. **StepCompletion** - Audit log entry (e.g., "H2S Check completed Feb 8 at 2pm, on-schedule")
   - Records when step was actually completed
   - Supports skipping with justification
   - Flags late/early completion

### Key Design Choices

- ✅ **Criticality-based**: Steps weighted by importance (H2S check = 2.0x, visual = 0.5x)
- ✅ **Flexible timing**: Tolerance windows per step (±4 hours vs ±5 days)
- ✅ **Skip support**: Allows justified skips (condition not met) vs unjustified (forgotten)
- ✅ **Multi-tenancy**: Winery isolation enforced at DB level
- ✅ **Audit trail**: Every step completion logged with timestamp + user

### Database Schema

```sql
-- 4 core tables + indexes
fermentation_protocols (templates)
protocol_steps (steps within template)
protocol_executions (fermentation → protocol assignment)
step_completions (audit log)
```

### Implementation Details

See [ADR-035](ADR-035-protocol-data-model-schema.md) for:
- Full entity definitions with Python classes
- SQL schema with constraints
- Migration path from design to production

---

## 📊 ADR-036: Compliance Scoring Algorithm

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 4-5 (after domain models in place)  
**Dependencies**: ADR-035 (requires ProtocolExecution model)

### What This Decides

**How to calculate protocol compliance score** (0-100%) for a fermentation:

```
COMPLIANCE_SCORE = (WEIGHTED_COMPLETION × 0.7) + (TIMING_SCORE × 0.3)
```

Where:
- **Weighted Completion** = steps completed × criticality multiplier
  - Critical step: 150 points max (1.5× multiplier)
  - Optional step: 50 points max (0.5× multiplier)
  - Justified skip: 60% credit
  - Unjustified skip: 0% credit
  - Late penalty: -10% to -50% depending on how late

- **Timing Score** = % of completed steps that were on-schedule

### Example Calculation

**Cabernet Sauvignon, Day 12 of 28:**

| Step | Type | Critical | Max | Status | Earned | Notes |
|------|------|----------|-----|--------|--------|-------|
| 1 | Yeast | ✓ | 150 | ✓ On-time | 150 | Day 0 |
| 2 | H2S | ✓ | 150 | ✓ 1 day late | 112 | -25% penalty |
| 3 | DAP | ✓ | 150 | ✓ On-time | 150 | Day 3 |
| 4 | Punch | ✗ | 50 | ✓ On-time | 50 | |
| 5 | Temp | ✗ | 50 | ✗ Justified skip | 30 | 60% credit |
| 6-7 | Future | - | 100 | ⏳ Pending | 0 | Not yet |

**Score**: (492/650) × 0.7 + 100% × 0.3 = **83%**

### Key Design Choices

- ✅ **Weighted by criticality**: H2S weight ≠ visual inspection weight
- ✅ **Timing matters**: 30% of score based on on-schedule completion
- ✅ **Justified skips allowed**: Don't penalize smart decisions
- ✅ **Real-time calculation**: Score updates as steps complete
- ✅ **Critical step bonus**: +5% if all critical steps done
- ✅ **Critical step penalty**: -15% if any critical step missing

### Winemaker Transparency

Every score shows:
- Which steps contributed how many points
- Why each step got its score
- What actions would improve score (complete pending step, reschedule late step)

### Implementation Details

See [ADR-036](ADR-036-compliance-scoring-algorithm.md) for:
- Complete Python functions with pseudocode
- Step-by-step calculation walkthrough
- Unit tests covering edge cases
- Performance considerations (sub-100ms calculation)

---

## 🔗 ADR-037: Protocol-Analysis Engine Integration

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 6-7 (after both engines exist)  
**Dependencies**: ADR-036 (compliance score), ADR-020 (analysis engine)

### What This Decides

**How Protocol and Analysis engines talk to each other** (bidirectional):

#### Protocol → Analysis (Confidence Boost)
```
Base Anomaly Confidence: 75% (from sample data quality)
Protocol Compliance: 87% → multiplier = 1.37
Final Confidence: 75% × 1.37 = 103% → capped at 100%

Explanation: "Confidence boosted from 75% to 100% due to good protocol compliance"
```

When protocol compliance is high, we trust Analysis predictions more.
When protocol compliance is low, we reduce Analysis confidence.

#### Analysis → Protocol (Advisory)
```
Anomaly: H2S detected (high confidence)
↓
Advisory: "Accelerate H2S_CHECK step immediately"
↓
Winemaker sees: "Analysis suggests H2S check - do it now"
↓
Winemaker action: Complete H2S check early
```

Analysis watches for patterns and suggests protocol changes.

### Use Cases

1. **Volatile temperature** → Increase temperature check frequency
2. **Stuck fermentation** → Accelerate nutrient addition step
3. **H2S smell detected** → Suggest aeration/punch-down immediately
4. **Early completion** → Can skip remaining minor steps

### Implementation Details

See [ADR-037](ADR-037-protocol-analysis-integration.md) for:
- Confidence multiplier formula
- Advisory generation logic
- Event system architecture
- Integration tests

---

## 🚨 ADR-038: Deviation Detection Strategy

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 5-6 (before alerts in ADR-040)  
**Dependencies**: ADR-035 (data model), ADR-036 (scoring)

### What This Decides

**How to detect and categorize deviations** from planned protocol:

#### 1. Timing Deviations
- **Late**: Step completed after tolerance window
  - Critical step 3 days late = CRITICAL deviation
  - Optional step 3 days late = MEDIUM deviation
- **Early**: Step completed before expected (rare but flagged)

#### 2. Skip Deviations
- **Justified**: "pH already optimal, no need to check"
  - SkipReason: CONDITION_NOT_MET, FERMENTATION_ENDED, WINEMAKER_DECISION
  - Allowed, earns 60% score credit
- **Unjustified**: "Forgot to punch down", "Equipment failure"
  - SkipReason: EQUIPMENT_FAILURE, OTHER
  - Not allowed, earns 0% score credit, triggers investigation

#### 3. Execution Quality Deviations
- **Missing data**: Step completed but no observations recorded
- **Pattern anomaly**: Related steps have unusual pattern (e.g., H2S check done but temp check skipped)

### Real-Time Detection Workflow

```
Step Completed
    ↓
Detect Timing Deviation
    ↓ (if late + critical)
ALERT: High severity
    ↓
Detect Skip Deviation
    ↓ (if unjustified)
Flag: Requires investigation
    ↓
Detect Quality Issues
    ↓
Update Compliance Score
    ↓
Trigger Analysis Recalibration
```

### Key Design Choices

- ✅ **Severity-based**: CRITICAL/HIGH/MEDIUM/LOW (not all deviations equal)
- ✅ **Immediate detection**: Flagged when step recorded, not at end
- ✅ **Winemaker acknowledgment**: Can explain deviations
- ✅ **Audit trail**: All deviations logged with context
- ✅ **Analysis integration**: Deviations feed into anomaly confidence

### Implementation Details

See [ADR-038](ADR-038-deviation-detection-strategy.md) for:
- Deviation detection algorithms
- Severity classification logic
- Database schema for deviation storage
- Unit tests for edge cases

---

## 📚 ADR-039: Protocol Template Management & Customization

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 3-4 (foundational governance)  
**Dependencies**: ADR-035 (data model)

### What This Decides

**How to manage protocol templates** (reusable definitions) vs instances (fermentation-specific):

#### Template Lifecycle

```
DRAFT         FINAL          DEPRECATED
↓             ↓              ↓
Admin creates, Admin approves  Replaced by
edits steps   (ready to use)   newer version
```

#### Instance Lifecycle

```
Template (parent)
    ↓ Copy for specific fermentation
Instance (child, customizable)
    ↓ Can modify steps before fermentation starts
Execution (immutable)
    ↓ Fermentation begins, track completions
```

### Operations

1. **Create Template** (Admin-only)
   - Define standard protocol for varietal (e.g., "Cabernet v2.0")
   - Add steps with criticality, timing, dependencies
   - State: DRAFT

2. **Approve Template** (Admin-only)
   - Review, validate steps
   - Transition: DRAFT → FINAL (ready to use)

3. **Create Instance** (Winemaker+)
   - Copy template for specific fermentation
   - Automatically assign protocol to fermentation

4. **Customize Steps** (Winemaker, before execution)
   - Adjust tolerance windows (±6 hours → ±8 hours)
   - Adjust timing (Day 5 → Day 6)
   - Add notes to steps
   - NOT allowed: Add/remove entire steps

5. **Create Version** (Admin-only)
   - Create new version (v1.0 → v2.0)
   - Deprecate old version
   - Track protocol evolution

### Key Design Choices

- ✅ **Reuse**: Templates prevent re-entering same steps
- ✅ **Governance**: Admin approval prevents bad protocols
- ✅ **Flexibility**: Winemakers can customize for conditions
- ✅ **Immutability**: Once fermentation starts, can't change protocol
- ✅ **Versioning**: Track protocol changes over time

### Implementation Details

See [ADR-039](ADR-039-protocol-template-management.md) for:
- State management and transitions
- API endpoints (create, approve, assign, customize)
- Database schema with versioning
- Unit tests

---

## 🔔 ADR-040: Notifications & Alerts Strategy

**Status**: ✅ Approved for Implementation  
**Timeline**: Week 7-9 (**Offline-First Priority**)  
**Dependencies**: ADR-038 (deviations trigger alerts)

### What This Decides

**How to alert winemakers to protocol issues** across multiple channels with offline-first support:

#### Alert Severities & Channels

| Severity | Examples | Channels | Timing |
|----------|----------|----------|--------|
| **CRITICAL** | H2S detected, fermentation stalled | In-app + SMS | Immediate |
| **HIGH** | Critical step 1+ days late | In-app + Email | Same-day |
| **MEDIUM** | Step due soon, deviation detected | In-app + Email | Routine |
| **LOW** | Step completed, informational | In-app only | Archived |

#### Alert Flow

```
Event Source (Deviation, Analysis, Scheduler)
    ↓
Alert Generator (determine severity, route channels)
    ↓
         ├─ In-App (WebSocket + polling fallback, cached for offline)
         ├─ SMS (Twilio, CRITICAL+HIGH only)
         └─ Email (async queue, all severities)
    ↓
Mobile App (pull cached alerts, works offline, sync on reconnect)
```

### Offline-First Design (7-day/week coverage requirement)

```
Mobile App (Winery Floor)
    ↓ On startup
Sync cached alerts from last 7 days
    ↓ No internet?
Show cached alerts (still useful without connectivity)
    ↓ User acknowledges alert
Save locally, sync when reconnected
    ↓ Internet returns
Push local changes to server
```

### User Preferences

- Quiet hours (e.g., 22:00-06:00, CRITICAL alerts still go through)
- Do Not Disturb (DND until X time)
- Channel preferences (SMS only for CRITICAL, email for all, etc.)
- Suppress LOW severity alerts

### Key Design Choices

- ✅ **Offline-first**: Mobile app works without connectivity
- ✅ **Severity-based routing**: SMS only for CRITICAL/HIGH
- ✅ **Real-time**: WebSocket for instant in-app, polling fallback
- ✅ **Schedulable**: Upcoming steps checked every 6 hours
- ✅ **Respects preferences**: Quiet hours, DND, channel prefs
- ✅ **Audit trail**: All alerts logged, searchable

### Implementation Details

See [ADR-040](ADR-040-notifications-alerts.md) for:
- Alert classification (CRITICAL/HIGH/MEDIUM/LOW)
- Channel implementations (WebSocket, SMS/Twilio, Email queue)
- Offline-first caching strategy
- User preference system
- Unit tests

---

## 🚀 Integration Timeline & Phases

### Phase 0: Data Model (Week 1-2)
**Goal**: Database and domain layer ready

- [x] ADR-035: Create tables (fermentation_protocols, protocol_steps, etc.)
- [x] ADR-035: Create Python domain models
- [x] ADR-035: Write migration scripts
- [ ] Load seed data from Susana's protocol PDFs

### Phase 1: Repository Layer (Week 2-3)
**Goal**: CRUD operations

- [ ] ProtocolRepository (CRUD for protocols)
- [ ] ProtocolStepRepository (CRUD for steps)
- [ ] ExecutionRepository (CRUD for executions)
- [ ] CompletionRepository (CRUD for completions)
- [ ] 100+ repository unit tests

### Phase 2: Service Layer (Week 4-6)
**Goal**: Business logic

- [ ] ADR-036: ComplianceScorer service
- [ ] ADR-038: DeviationDetector service
- [ ] ADR-039: TemplateManager service
- [ ] ProtocolService (orchestrator)
- [ ] Integration tests with sample data

### Phase 3: API Layer (Week 7-8)
**Goal**: REST endpoints

- [ ] Protocol CRUD endpoints
- [ ] Template approval workflow
- [ ] Step completion recording
- [ ] Compliance score queries
- [ ] API documentation

### Phase 4: Integration & Alerts (Week 8-9)
**Goal**: Tie to Analysis + Alerts

- [ ] ADR-037: Confidence boost function
- [ ] ADR-037: Advisory generation
- [ ] ADR-040: Alert generation and routing
- [ ] ADR-040: Offline-first mobile sync
- [ ] End-to-end integration tests

### Phase 5: UI & Polish (Week 9-10)
**Goal**: May demo ready

- [ ] Dashboard showing protocol status
- [ ] Protocol assignment UI
- [ ] Step completion recording UI
- [ ] Alert display + acknowledgment
- [ ] Mobile app refinement
- [ ] Demo scenario testing

---

## 📚 Related ADRs (Foundation)

These ADRs provide supporting infrastructure:

- **ADR-021**: Protocol Compliance Engine (vision/overview)
- **ADR-020**: Analysis Engine Architecture (partner system)
- **ADR-025**: Multi-Tenancy Security (winery isolation)
- **ADR-026**: Error Handling Strategy (exception handling)
- **ADR-027**: Structured Logging & Observability (audit trail)

---

## ✅ Validation Checklist

Before implementation:
- [ ] Review all 6 ADRs with Susana (AI enologist)
- [ ] Confirm protocol PDF data available and convertible
- [ ] Clarify critical vs optional steps per varietal
- [ ] Confirm tolerance windows (±N hours vs ±N days)
- [ ] Clarify skip justification rules
- [ ] Confirm alert channels (SMS cost acceptable?)
- [ ] Test mobile app offline capabilities

---

## 🎯 Success Criteria

By May 2026 demo:

✅ **Protocol Definition**
- [x] Template library for common varietals (CS, PN, CH, etc.)
- [x] Each template with 15-40 steps, criticality scoring
- [x] Version tracking (v1.0, v2.0, etc.)

✅ **Protocol Execution**
- [x] Fermentations assigned protocols at start
- [x] Winemakers can log step completions
- [x] System calculates compliance score in real-time
- [x] Deviations detected and logged

✅ **Integration**
- [x] Protocol compliance → Analysis confidence adjustment
- [x] Analysis anomalies → Protocol advisories
- [x] All data flow tested end-to-end

✅ **Alerts & Mobile**
- [x] Critical alerts reach winemakers immediately (SMS/email/in-app)
- [x] Mobile app works offline (cached alerts visible)
- [x] Alert acknowledgment works with eventual sync
- [x] User preferences respected (quiet hours, DND, etc.)

✅ **Demo Scenario**
- [x] Load real Cabernet protocol (from Susana's PDFs)
- [x] Create fermentation, assign protocol
- [x] Simulate 3-5 days of protocol execution
- [x] Show compliance score evolution
- [x] Show deviations detected and alerts sent
- [x] Show Analysis confidence boosted by high compliance

---

## 📖 How to Use This Document

**For Developers**: Read ADRs in order (035 → 036 → 037 → 038 → 039 → 040) to understand dependencies.

**For Architects**: Use the integration timeline (Phases 0-5) to plan sprints.

**For Testing**: Each ADR has a "Testing Strategy" section with unit test examples.

**For Validation**: Use the "Validation Checklist" before starting implementation.

---

## 💬 Questions & Next Steps

1. **Protocol PDFs**: When can these be converted to JSON/CSV for seed data?
2. **Enologist Review**: Can Susana review these 6 ADRs for accuracy?
3. **Timeline Feasibility**: Are 10 weeks realistic for all 5 phases + full system?
4. **Mobile App**: What frameworks for iOS/Android? (React Native? Flutter?)
5. **Demo Focus**: Which varietal for May demo? (Cabernet recommended for complexity)

