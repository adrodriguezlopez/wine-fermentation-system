# Protocol Engine - Developer Quick Reference

**Quick Navigation for Developers**  
**Print-Friendly Format**

---

## 📚 The 6 ADRs at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│ ADR-035: DATA MODEL                                         │
│ 4 Tables: Protocols, Steps, Executions, Completions         │
│ Domain: FermentationProtocol, ProtocolStep, ...             │
│ Time: Week 1-2                                              │
│ Status: Ready to build                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ADR-039: TEMPLATE MANAGEMENT                                │
│ Operations: Create, Approve, Assign, Customize, Version     │
│ Governance: Admin templates → Winemaker instances           │
│ Time: Week 3-4                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ADR-036: COMPLIANCE SCORING                                 │
│ Formula: 70% completion + 30% timing                        │
│ Weighted: Critical 1.5x, normal 1.0x, optional 0.5x        │
│ Time: Week 4-5                                              │
└─────────────────────────────────────────────────────────────┘
                     ↙            ↘
        ┌───────────────────────────────────┐
        │ ADR-038: DEVIATIONS              │
        │ Detect: Timing, Skip, Quality    │
        │ Time: Week 5-6                   │
        └───────────────────────────────────┘
                     ↓
        ┌───────────────────────────────────┐
        │ ADR-037: ANALYSIS INTEGRATION    │
        │ Confidence boost + Advisories    │
        │ Time: Week 6-7                   │
        └───────────────────────────────────┘
                     ↓
        ┌───────────────────────────────────┐
        │ ADR-040: ALERTS                   │
        │ SMS/Email/In-app, Offline-first  │
        │ Time: Week 7-9                   │
        └───────────────────────────────────┘
                     ↓
        ┌───────────────────────────────────┐
        │ UI + Mobile (Weeks 9-10)          │
        │ Dashboard, Assignment, Demo       │
        └───────────────────────────────────┘
```

---

## 🔧 Core Entities (ADR-035)

```python
# Master template
FermentationProtocol
├── varietal_code: "CS", "PN", "CH"
├── version: "1.0", "2.0"
├── expected_duration_days: 28
├── state: DRAFT, FINAL, DEPRECATED
├── is_template: bool
└── steps: List[ProtocolStep]

# Single step
ProtocolStep
├── step_order: 1, 2, 3
├── step_type: YEAST_INOCULATION, H2S_CHECK, DAP_ADDITION
├── expected_day: 0, 3, 5
├── tolerance_hours: 6, 12, 72
├── is_critical: bool
├── criticality_score: 0.5-2.0
└── depends_on_step_id: Optional[int]

# Per-fermentation tracking
ProtocolExecution
├── fermentation_id: int
├── protocol_id: int
├── compliance_score: 0-100
├── status: NOT_STARTED, ACTIVE, COMPLETED
└── completions: List[StepCompletion]

# Audit log
StepCompletion
├── execution_id: int
├── step_id: int
├── completed_at: datetime
├── is_on_schedule: bool
├── was_skipped: bool
└── skip_reason: Optional[SkipReason]
```

---

## 📊 Compliance Score Formula (ADR-036)

```
COMPLIANCE_SCORE = (WEIGHTED_COMPLETION × 0.7) + (TIMING_SCORE × 0.3)

Per-Step Points:
├─ Completed on-time: 100% of possible points
├─ Completed 1 day late: -25% penalty
├─ Completed 2+ days late: -50% penalty
├─ Justified skip: 60% of possible points
├─ Unjustified skip: 0% of points
└─ Not completed: 0% of points

Criticality Weighting:
├─ Critical step: 1.5× multiplier (150 pts max)
├─ Normal step: 1.0× multiplier (100 pts max)
└─ Optional step: 0.5× multiplier (50 pts max)

Bonuses:
├─ All critical steps done: +5% bonus
└─ Any critical step missing: -15% penalty

Result: 0-100 (CRITICAL completions matter most)
```

---

## 🚨 Deviation Types (ADR-038)

```
TIMING DEVIATIONS
├─ Late + Critical + 3 days → CRITICAL severity
├─ Late + Optional + 3 days → MEDIUM severity
└─ Early by >1 day → MEDIUM severity

SKIP DEVIATIONS
├─ Justified (pH optimal, ferment done) → No deviation
└─ Unjustified (forgot, equipment) → Requires investigation

QUALITY DEVIATIONS
├─ Missing data (no BRIX value recorded)
└─ Pattern anomaly (H2S done, temp check nearby skipped)

Detection: Real-time when step recorded
Response: Flag severity → Alert winemaker → Recalibrate analysis
```

---

## 📤 Alert Severity & Channels (ADR-040)

```
CRITICAL
├─ Examples: H2S detected, fermentation stalled, equipment failure
├─ Channels: In-app + SMS (immediate)
└─ Users: All winemakers

HIGH
├─ Examples: Critical step 1+ days late
├─ Channels: In-app + Email (same-day)
└─ Users: All winemakers

MEDIUM
├─ Examples: Step due in 12 hours, deviation detected
├─ Channels: In-app + Email (routine)
└─ Users: All winemakers

LOW
├─ Examples: Step completed, info only
├─ Channels: In-app only (archived)
└─ Users: On-demand only

Offline-First:
├─ Cache: CRITICAL, HIGH, MEDIUM (mobile app)
├─ Sync: When internet returns
└─ Override: CRITICAL alerts bypass quiet hours/DND
```

---

## 🔗 API Endpoints Summary

```
TEMPLATES (Admin-only)
├─ POST /protocol-templates (create DRAFT)
├─ GET /protocol-templates/{varietal}
├─ POST /protocol-templates/{id}/approve (DRAFT→FINAL)
└─ POST /protocol-templates/{id}/version (create v2.0)

INSTANCES (Winemaker+)
├─ POST /protocol-instances (copy template)
├─ GET /fermentations/{id}/protocol (get current)
└─ POST /protocol-instances/{id}/customize (adjust steps)

EXECUTION (Winemaker)
├─ POST /protocol-executions/{id}/steps (log step)
├─ GET /fermentations/{id}/compliance-score
├─ GET /fermentations/{id}/protocol-deviations
└─ GET /fermentations/{id}/alerts/cached (offline sync)

ALERTS (All users)
├─ GET /alerts/{winery_id}
└─ POST /alerts/{id}/acknowledge
```

---

## 🧪 Essential Tests by ADR

```
ADR-035 (Data Model):
├─ FermentationProtocol creation + validation
├─ ProtocolStep ordering + dependency checks
├─ ProtocolExecution state transitions
└─ StepCompletion audit trail (20+ tests)

ADR-036 (Scoring):
├─ Perfect execution: 100%
├─ One critical step late: <85%
├─ Justified skip: >60%
├─ Unjustified skip: <50%
└─ Mixed scenarios (15+ tests)

ADR-038 (Deviations):
├─ Timing: late critical → CRITICAL severity
├─ Skip: unjustified → investigation required
├─ Quality: missing data → flagged
└─ Accumulation: multiple deviations (12+ tests)

ADR-039 (Templates):
├─ Create DRAFT template
├─ Approve DRAFT → FINAL
├─ Create instance from FINAL
├─ Cannot customize after execution starts
└─ Version creation (10+ tests)

ADR-040 (Alerts):
├─ CRITICAL alerts → SMS sent
├─ HIGH alerts → Email sent
├─ LOW alerts → In-app only
├─ Quiet hours respected for non-CRITICAL
└─ Offline cache working (15+ tests)
```

---

## 📋 Database Schema Outline

```sql
-- Core tables (ADR-035)
fermentation_protocols (templates)
├─ Keys: winery_id, varietal_code, version (UNIQUE)
├─ Fields: protocol_name, state, is_template, template_id
└─ Indexes: (winery_id, is_active), (varietal_code)

protocol_steps (steps within template)
├─ Keys: protocol_id, step_order (UNIQUE)
├─ Fields: step_type, expected_day, tolerance_hours, is_critical
└─ Indexes: (protocol_id)

protocol_executions (fermentation → protocol)
├─ Keys: fermentation_id (UNIQUE)
├─ Fields: compliance_score, completed_steps, status
└─ Indexes: (winery_id, status), (fermentation_id)

step_completions (audit log)
├─ Keys: execution_id, step_id, completed_at
├─ Fields: is_on_schedule, was_skipped, skip_reason
└─ Indexes: (execution_id), (completed_at)

-- Deviation tables (ADR-038)
timing_deviations
skip_deviations
execution_deviations

-- Alert tables (ADR-040)
alerts
cached_alerts (for offline-first mobile)
alert_preferences (user settings)
```

---

## 🎯 Weekly Checklist

```
WEEK 1-2: DATA MODEL (ADR-035)
├─ [ ] Create tables (Alembic migration)
├─ [ ] Create Python domain models
├─ [ ] Create repositories
├─ [ ] Load seed protocols from Susana's PDFs
└─ [ ] Repository tests (100 coverage)

WEEK 3-4: TEMPLATE MANAGEMENT (ADR-039)
├─ [ ] TemplateService (create, approve, version)
├─ [ ] InstanceService (copy, customize)
├─ [ ] API endpoints
└─ [ ] Service tests (100 coverage)

WEEK 4-5: COMPLIANCE SCORING (ADR-036)
├─ [ ] ComplianceScorer service
├─ [ ] Implement formula (weighted + timing)
├─ [ ] Real-time updates
└─ [ ] Scoring tests (50+ test cases)

WEEK 5-6: DEVIATION DETECTION (ADR-038)
├─ [ ] DeviationDetector service
├─ [ ] Timing/skip/quality detection
├─ [ ] Severity classification
└─ [ ] Integration with completion recording

WEEK 6-7: ANALYSIS INTEGRATION (ADR-037)
├─ [ ] Confidence boost function
├─ [ ] Advisory generation
├─ [ ] Event system
└─ [ ] Integration tests (end-to-end)

WEEK 7-9: ALERTS & NOTIFICATIONS (ADR-040)
├─ [ ] Alert model + repository
├─ [ ] In-app WebSocket
├─ [ ] SMS integration (Twilio)
├─ [ ] Email queue
├─ [ ] Offline-first caching
└─ [ ] Mobile sync endpoints

WEEK 9-10: UI & DEMO
├─ [ ] Dashboard UI
├─ [ ] Assignment UI
├─ [ ] Step logging UI
├─ [ ] Alert display
├─ [ ] Mobile app refinement
└─ [ ] Demo scenario testing
```

---

## 🔑 Key Constants

```python
# Criticality Multipliers
CRITICALITY_CRITICAL = 1.5      # 150 points max
CRITICALITY_NORMAL = 1.0        # 100 points max
CRITICALITY_OPTIONAL = 0.5      # 50 points max

# Score Weights
WEIGHT_COMPLETION = 0.7         # 70%
WEIGHT_TIMING = 0.3             # 30%

# Penalties
LATE_1_DAY = -0.10              # -10%
LATE_2_PLUS_DAYS = -0.25        # -25% to -50%
UNJUSTIFIED_SKIP = 0.0          # 0%
JUSTIFIED_SKIP = 0.60           # 60% credit

# Bonuses
ALL_CRITICAL_DONE = +0.05       # +5%
MISSING_CRITICAL = -0.15        # -15%

# Alert Severities
CRITICAL_WINDOW = 0             # Immediate
HIGH_WINDOW = 1                 # Same-day
MEDIUM_WINDOW = 7               # Week
LOW_WINDOW = 30                 # Archive

# Offline Cache
CACHE_EXPIRES_DAYS = 7
CACHE_SYNC_INTERVAL_HOURS = 6
```

---

## 🚀 Run This First

```bash
# Check existing fermentation module
pytest tests/unit/fermentation -v

# Verify database connection
python -c "from sqlalchemy import create_engine; \
  engine = create_engine(os.env['DATABASE_URL']); \
  connection = engine.connect(); \
  print('Database connection successful')"

# Check FastAPI is running
curl http://localhost:8000/docs

# Then start Week 1: Create ADR-035 tables
alembic upgrade head
```

---

## 📞 Quick Links

**Full Documentation**:
- [PROTOCOL-ADR-GUIDE.md](PROTOCOL-ADR-GUIDE.md) - Complete guide
- [ADR-035](ADR-035-protocol-data-model-schema.md) - Data model
- [ADR-036](ADR-036-compliance-scoring-algorithm.md) - Scoring
- [ADR-037](ADR-037-protocol-analysis-integration.md) - Integration
- [ADR-038](ADR-038-deviation-detection-strategy.md) - Deviations
- [ADR-039](ADR-039-protocol-template-management.md) - Templates
- [ADR-040](ADR-040-notifications-alerts.md) - Alerts

**Reference**:
- [PROTOCOL-IMPLEMENTATION-SUMMARY.md](PROTOCOL-IMPLEMENTATION-SUMMARY.md) - Overview
- [PROTOCOL-IMPLEMENTATION-CHECKLIST.md](PROTOCOL-IMPLEMENTATION-CHECKLIST.md) - Pre-implementation tasks

**Status**:
- [ADR-INDEX.md](ADR-INDEX.md) - Full ADR index

---

## ✅ Ready to Build?

All 6 ADRs are **approved and implementation-ready**.

**Start with**: ADR-035 (Data Model) in Week 1-2  
**Follow with**: Template → Scoring → Deviations → Analysis → Alerts (Weeks 3-9)  
**Finish with**: UI & Demo refinement (Weeks 9-10)  

**Questions?** Check the full ADR document for that topic.

**Need clarification?** Review PROTOCOL-ADR-GUIDE.md → Validation Checklist.

**Let's ship it! 🍷**

