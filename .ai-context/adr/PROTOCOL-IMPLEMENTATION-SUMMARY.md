# Protocol Implementation ADRs - Summary

**Created**: February 9, 2026  
**Status**: ✅ Ready for Review & Implementation  
**Scope**: 6 new ADRs (ADR-035 through ADR-040) for Protocol Compliance Engine  
**Timeline**: 10 weeks (Week 1-10) to May 2026 demo

---

## 📦 What Was Created

### 6 New Architecture Decision Records

| # | ADR | Title | Focus | File |
|---|-----|-------|-------|------|
| 1 | ADR-035 | Protocol Data Model & Schema | Domain entities, 4 core tables | `ADR-035-protocol-data-model-schema.md` |
| 2 | ADR-036 | Compliance Scoring Algorithm | Score calculation (70% completion + 30% timing) | `ADR-036-compliance-scoring-algorithm.md` |
| 3 | ADR-037 | Protocol-Analysis Integration | Bidirectional integration (confidence boost + advisories) | `ADR-037-protocol-analysis-integration.md` |
| 4 | ADR-038 | Deviation Detection Strategy | Detect timing/skip/quality deviations | `ADR-038-deviation-detection-strategy.md` |
| 5 | ADR-039 | Template Management & Customization | Reusable templates → per-fermentation instances | `ADR-039-protocol-template-management.md` |
| 6 | ADR-040 | Notifications & Alerts | Real-time alerts, offline-first mobile | `ADR-040-notifications-alerts.md` |

### Supporting Documentation

- **PROTOCOL-ADR-GUIDE.md**: Navigation, dependencies, timeline, validation checklist

---

## 🎯 What Each ADR Solves

### ADR-035: Data Model
**Problem**: How to structure protocol data?  
**Solution**: 
- **FermentationProtocol**: Master templates with versioning
- **ProtocolStep**: Ordered steps with criticality scoring & tolerance windows
- **ProtocolExecution**: Per-fermentation tracking with compliance score
- **StepCompletion**: Audit log for every step

**Why It Matters**: Clean schema enables compliance scoring, deviation detection, and audit trails.

---

### ADR-036: Compliance Scoring
**Problem**: How to measure protocol adherence?  
**Solution**:
```
COMPLIANCE_SCORE = (WEIGHTED_COMPLETION × 0.7) + (TIMING_SCORE × 0.3)
```
- Critical steps worth more (150 pts) than optional (50 pts)
- Late penalties: -10% to -50% depending on how late
- Justified skips: 60% credit; unjustified: 0%
- Real-time calculation (updates as steps complete)

**Example**: Cabernet with mixed compliance → 83% score (from detailed walkthrough)

**Why It Matters**: Winemakers see exactly why score is 83%, not 85%. Transparency builds trust.

---

### ADR-037: Analysis Integration
**Problem**: How do Protocol and Analysis engines talk?  
**Solution**:
- **Protocol → Analysis**: Compliance score boosts anomaly confidence
  - High compliance (87%) → confidence multiplier 1.37× → more confident predictions
  - Low compliance (45%) → multiplier 0.95× → less confident predictions
- **Analysis → Protocol**: Anomalies suggest protocol changes
  - H2S detected → "Accelerate H2S_CHECK step"
  - Stuck fermentation → "Accelerate DAP_ADDITION step"

**Why It Matters**: Two systems informed by each other = better decision-making.

---

### ADR-038: Deviation Detection
**Problem**: How to catch protocol problems early?  
**Solution**: Real-time detection of 3 types:
1. **Timing Deviations**: Late/early step completion
   - Critical + 3 days late = CRITICAL severity
2. **Skip Deviations**: Unjustified skips (forgot to punch down)
   - Justified: "pH already optimal" → allowed
   - Unjustified: "Equipment failure" → requires investigation
3. **Quality Deviations**: Missing data or unusual patterns

**Workflow**: Step recorded → detect deviations → flag severity → alert winemaker → recalibrate analysis

**Why It Matters**: Problems caught day-of, not at end of fermentation.

---

### ADR-039: Template Management
**Problem**: How to reuse protocols across multiple fermentations?  
**Solution**: Two-level hierarchy:
- **Templates** (admin-only, DRAFT → FINAL → DEPRECATED)
  - Master definitions (e.g., "Cabernet Sauvignon v2.0")
  - Version-tracked (v1.0 → v2.0 for learnings)
- **Instances** (winemaker-assignable, customizable before execution)
  - Copy of template for specific fermentation
  - Can adjust tolerance windows, timing, add notes
  - Locked once fermentation starts

**Why It Matters**: No more re-entering protocols. Winemakers get flexibility within governance.

---

### ADR-040: Notifications & Alerts
**Problem**: How to reach winemakers 7-day/week with protocol issues?  
**Solution**: Multi-channel, severity-based, offline-first:

| Severity | Channels | Timing |
|----------|----------|--------|
| CRITICAL | In-app + SMS | Immediate |
| HIGH | In-app + Email | Same-day |
| MEDIUM | In-app + Email | Routine |
| LOW | In-app only | Archived |

**Offline-First**: Mobile app caches CRITICAL/HIGH/MEDIUM alerts, works without internet.  
**Preferences**: Users set quiet hours, DND, channel preferences.

**Why It Matters**: Winemakers see issues regardless of internet connectivity or time of day.

---

## 🔄 How They Work Together

```
Week 1-2: Build data model (ADR-035)
    ↓
Week 3-4: Build template management (ADR-039)
    ↓
Week 4-5: Build scoring algorithm (ADR-036)
    ↓
Week 5-6: Build deviation detection (ADR-038)
    ↓
Week 6-7: Build analysis integration (ADR-037)
    ↓
Week 7-9: Build alerts & notifications (ADR-040)
    ↓
Week 9-10: UI, mobile, demo refinement
```

Each ADR is designed to integrate with previous ones. By week 10, everything works together.

---

## 🎓 Key Design Principles (Repeated Across All ADRs)

### 1. **Transparency**
- Winemakers see why compliance is 83%, not 85%
- Every deviation logged with context
- Every alert shows recommended action

### 2. **Offline-First**
- Mobile app works without connectivity (critical for winery floor)
- Data syncs when internet returns
- CRITICAL alerts still reach winemakers somehow (SMS if app offline)

### 3. **Flexible + Governed**
- Admins control templates (DRAFT → FINAL approval)
- Winemakers can customize instances (but not templates)
- Once fermentation starts, protocol is locked

### 4. **Multi-Tenancy Safe**
- Winery isolation enforced at DB level
- Every query scoped by winery_id
- No cross-winery data leakage

### 5. **Audit Trail**
- Every action logged (step completed, deviation detected, alert sent)
- Searchable by fermentation, user, date
- Required for regulatory compliance (winery records)

---

## 📊 By The Numbers

### Data Structures
- 4 core tables (protocols, steps, executions, completions)
- 3 deviation tables (timing, skip, execution)
- 2 alert tables (Alert, CachedAlert)
- 2 preference tables (UserPreference, ProtocolChange)
- ~12 total tables with indexes

### Scoring
- ~100 lines of Python for compliance calculation
- Execution time: <100ms per fermentation
- Weights: 70% completion, 30% timing
- Multipliers: 0.5 to 2.0 per step based on criticality

### API Endpoints
- 15+ endpoints for template management
- 10+ endpoints for execution tracking
- 8+ endpoints for alerts/notifications
- All documented with OpenAPI

### Unit Tests
- 50+ test cases across 6 ADRs
- Coverage for happy path, edge cases, error handling
- Integration tests for cross-system interactions

---

## ✅ Validation & Next Steps

### Before Implementation

**Must Clarify with Susana**:
1. [ ] Review protocol PDFs - which varietal for seed data?
2. [ ] Confirm criticality weights - are steps weighted correctly?
3. [ ] Confirm tolerance windows - ±6 hours for H2S, ±3 days for racking?
4. [ ] Confirm skip rules - what makes skip "justified" vs "unjustified"?
5. [ ] Confirm alert preferences - SMS cost acceptable for CRITICAL alerts?

**Must Prepare**:
1. [ ] Convert protocol .docx files to JSON/CSV
2. [ ] Design seed data (5-10 complete protocol templates)
3. [ ] Prepare test fermentation scenarios

### Ready to Start

**Week 1 Actions**:
1. Create fermentation_protocols table (ADR-035)
2. Create Python domain models
3. Write migration script
4. Load seed data from protocols

**Week 2 Actions**:
1. Create ProtocolRepository with 100% test coverage
2. Create ProtocolStepRepository
3. Create ExecutionRepository
4. Create CompletionRepository

**Weeks 3-4 Actions**:
1. TemplateService (create, approve, version)
2. InstanceService (create from template, customize)

**Weeks 4-5 Actions**:
1. ComplianceScorer service
2. Scoring algorithm fully tested

**Weeks 5-6 Actions**:
1. DeviationDetector service
2. Real-time deviation detection
3. Deviation alerts

**Weeks 6-7 Actions**:
1. Protocol-Analysis bidirectional integration
2. Confidence boost function
3. Advisory generation

**Weeks 7-9 Actions**:
1. Alert generation + routing
2. SMS integration (Twilio)
3. Email queue system
4. Offline-first mobile caching

**Weeks 9-10 Actions**:
1. Dashboard UI
2. Mobile refinements
3. Demo scenario testing
4. Performance optimization

---

## 🎯 May Demo Scenario

**Goal**: Show complete Protocol Engine in action

**Setup**:
- Load Cabernet Sauvignon protocol (from Susana's PDF)
- Create fermentation "Napa Valley 2026 CS - Demo Lot"
- Assign Cabernet protocol to fermentation

**Execution**:
- Day 1: Log "Yeast Inoculation" step ✓
- Day 3: Log "DAP Addition" step ✓
- Day 5: Log "H2S Check" step (simulate late, day 6) ⚠️
- Day 7: Dashboard shows:
  - Compliance: 87% (good completion, one late step)
  - Deviation: "H2S Check 1 day late" (logged, not critical)
  - Alert: None (within acceptable range)
  - Confidence boost: "Analysis confidence 75% → 87% due to protocol compliance"

**UI Show**:
- Protocol template library (search by varietal, version)
- Fermentation assigned to protocol (showing status)
- Step completion UI (tap to mark complete, add notes)
- Compliance score trending (graph over 3-day period)
- Deviation timeline (what went off-track)
- Alert history (what alerts were sent)
- Mobile app showing offline-cached alerts

**Outcome**: Investors see Protocol Engine preventing problems before they become costly.

---

## 📋 Files Created

All files in: `c:\dev\wine-fermentation-system\.ai-context\adr\`

```
ADR-035-protocol-data-model-schema.md      (25 KB)
ADR-036-compliance-scoring-algorithm.md    (22 KB)
ADR-037-protocol-analysis-integration.md   (18 KB)
ADR-038-deviation-detection-strategy.md    (20 KB)
ADR-039-protocol-template-management.md    (24 KB)
ADR-040-notifications-alerts.md            (26 KB)
PROTOCOL-ADR-GUIDE.md                      (15 KB)
PROTOCOL-IMPLEMENTATION-SUMMARY.md         (this file, 8 KB)
```

**Total**: 158 KB of detailed architecture, pseudocode, schemas, and test cases.

---

## 🚀 Ready to Build

All ADRs are:
- ✅ Written with pseudocode (Python-focused)
- ✅ Include database schemas (SQL)
- ✅ Include API contracts (JSON examples)
- ✅ Include unit test examples
- ✅ Include integration points
- ✅ Include error handling
- ✅ Include edge cases
- ✅ Linked to related ADRs (ADR-020, ADR-025, ADR-027, etc.)
- ✅ Aligned with May 2026 deadline (10 weeks)
- ✅ Aligned with AI enologist requirements
- ✅ Aligned with 7-day/week coverage + offline-first constraints

**Next Step**: Review with Susana, clarify protocol questions, start Phase 0 (data model).

