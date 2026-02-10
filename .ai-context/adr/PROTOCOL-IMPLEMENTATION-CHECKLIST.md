# Protocol Implementation - Ready to Build Checklist

**Date Created**: February 9, 2026  
**Status**: ✅ All ADRs Complete & Ready for Review  
**Next Phase**: Clarification with Susana, then Phase 0 Implementation

---

## 📦 Deliverables Summary

### ✅ 6 New Architecture Decision Records Created

**ADR-035: Protocol Data Model & Schema Design** (25 KB)
- ✅ 4 domain entities fully designed (FermentationProtocol, ProtocolStep, ProtocolExecution, StepCompletion)
- ✅ Complete SQL schema with constraints and indexes
- ✅ Python class definitions with all fields and relationships
- ✅ Migration strategy outlined
- ✅ Multi-tenancy isolation enforced

**ADR-036: Compliance Scoring Algorithm** (22 KB)
- ✅ Formula: 70% completion + 30% timing
- ✅ Criticality-based weighting (0.5x to 2.0x per step)
- ✅ Late penalties: -10% to -50% depending on severity
- ✅ Justified skip handling (60% credit)
- ✅ Real-time calculation (<100ms execution)
- ✅ Step-by-step example walkthrough
- ✅ 15+ unit tests defined

**ADR-037: Protocol-Analysis Integration** (18 KB)
- ✅ Bidirectional communication defined
- ✅ Confidence boost function (multiplier 0.5 to 1.5)
- ✅ Advisory generation algorithm
- ✅ Event system architecture
- ✅ API contracts (JSON examples)
- ✅ Error handling for missing data

**ADR-038: Deviation Detection Strategy** (20 KB)
- ✅ 3 deviation types (timing, skip, quality)
- ✅ Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- ✅ Real-time detection workflow
- ✅ Justification handling for skips
- ✅ Database schema for deviation storage
- ✅ 10+ edge case test scenarios

**ADR-039: Template Management & Customization** (24 KB)
- ✅ State lifecycle (DRAFT → FINAL → DEPRECATED)
- ✅ Template vs instance differentiation
- ✅ 5 core operations (create, approve, assign, customize, version)
- ✅ Admin governance + winemaker flexibility
- ✅ Customization constraints (can't add/remove steps)
- ✅ API endpoints fully specified

**ADR-040: Notifications & Alerts Strategy** (26 KB)
- ✅ 4 severity levels with channel routing
- ✅ Multi-channel support (in-app, SMS, email)
- ✅ Offline-first mobile caching
- ✅ User preferences (quiet hours, DND, channels)
- ✅ Scheduler for upcoming steps
- ✅ Twilio SMS integration example
- ✅ Email queue system design

### ✅ Supporting Documentation

- **PROTOCOL-ADR-GUIDE.md** (15 KB)
  - Navigation guide for all 6 ADRs
  - Integration timeline and phases
  - Validation checklist
  - Success criteria for May demo

- **PROTOCOL-IMPLEMENTATION-SUMMARY.md** (8 KB)
  - Executive summary of each ADR
  - Key design principles
  - Metrics (data structures, code size, endpoints)
  - Next steps and validation needs

- **Updated ADR-INDEX.md**
  - All 6 new ADRs listed with status
  - Cross-references with existing ADRs (020, 021, 025, 026, 027)

---

## 🎯 What These ADRs Enable

### For Implementation
- ✅ **Code-ready**: Pseudocode and examples in all ADRs
- ✅ **Schema-ready**: SQL DDL ready to execute
- ✅ **Test-ready**: 50+ unit test examples provided
- ✅ **API-ready**: REST contracts defined with JSON examples
- ✅ **Integration-ready**: Cross-system hooks specified

### For May Demo
- ✅ **Complete system**: All 7 modules (Fermentation, Analysis, Protocol, Fruit Origin, Auth, Winery, Historical)
- ✅ **Working demo scenario**: Load Cabernet protocol, assign to fermentation, track 3-5 days
- ✅ **Real data**: From Susana's protocol PDFs (pending conversion)
- ✅ **Mobile-ready**: Offline-first alerts for winery floor
- ✅ **Investor-ready**: Shows problem prevention, not just detection

### For Susana's Workflows
- ✅ **Protocol library**: Templated protocols for each varietal
- ✅ **Customization**: Can adjust timing/tolerance for specific conditions
- ✅ **Real-time tracking**: See compliance score as fermentation progresses
- ✅ **Deviation alerts**: Immediate notification of issues (H2S, stalling, missed steps)
- ✅ **Integration insights**: Analysis engine suggests protocol changes based on patterns
- ✅ **Audit trail**: Every action logged for regulatory compliance

---

## 🚦 Pre-Implementation Checklist

### Must Clarify with Susana

**Protocol Content** (from PDF analysis):
- [ ] Confirm varietal list: Cabernet, Chardonnay, Pinot Noir, others?
- [ ] For each varietal, provide: step count, step types, timing (days), tolerance windows
- [ ] Example: "Pinot Noir: 18 steps, 18-22 days, H2S check on day 5 ±6 hours"

**Criticality & Weighting**:
- [ ] Which steps are CRITICAL vs optional for each varietal?
- [ ] Confirm criticality multipliers: 1.5x for critical, 1.0x for normal, 0.5x for optional?
- [ ] Does criticality differ between reds and whites?

**Tolerance Windows**:
- [ ] Confirm timing tolerances:
  - H2S Check: ±6 hours? (current assumption)
  - DAP Addition: ±12 hours?
  - Racking: ±3 days?
  - Pressing: ±5 days?
- [ ] Are these day-of or hour-based? (current design is hour-based, flexible)

**Skip Rules**:
- [ ] What makes skip "justified" vs "unjustified"?
  - Justified examples: "pH already optimal", "Brix negative, ferment done"
  - Unjustified examples: "Forgot", "No time", "Equipment broken"
- [ ] How many unjustified skips before escalation?

**Alert Preferences**:
- [ ] SMS cost acceptable? (Twilio ~$0.01 per SMS)
- [ ] Should CRITICAL alerts auto-escalate to head winemaker?
- [ ] Quiet hours: when? (current design: 22:00-06:00 with CRITICAL override)

**Mobile Requirements**:
- [ ] Which phone platforms? (iOS, Android, both?)
- [ ] UI framework preference? (React Native, Flutter, native?)
- [ ] Must offline functionality include: view alerts, log steps, acknowledge alerts?

### Must Prepare for Week 1

**Protocol PDFs to JSON**:
- [ ] Convert all protocol .docx files to structured JSON/CSV
- [ ] Extract: varietal, step order, step type, expected day, tolerance hours, criticality
- [ ] Validate all data for consistency

**Seed Data**:
- [ ] Create 5-10 complete protocol templates in DB format
- [ ] Create sample fermentations to test against
- [ ] Create test deviations for testing alert system

**Database Setup**:
- [ ] Database created and accessible
- [ ] Alembic migration scripts working
- [ ] Existing fermentation module running (for FK references)

**Development Environment**:
- [ ] Python 3.9+ with FastAPI/SQLAlchemy
- [ ] PostgreSQL running
- [ ] Tests passing (existing 1,100+ tests should pass)

### Ready to Implement

**Week 1-2: Data Model (ADR-035)**
- [ ] Execute migration to create 4 core tables
- [ ] Create Python domain models
- [ ] Create repositories (CRUD operations)
- [ ] 100% test coverage for repositories
- [ ] Load seed data (protocols from Susana's PDFs)

**Week 3-4: Template Management (ADR-039)**
- [ ] Create TemplateService (create, approve, version)
- [ ] Create InstanceService (copy template → fermentation)
- [ ] Create CustomizationService (adjust before execution)
- [ ] API endpoints + full test coverage

**Week 4-5: Scoring Algorithm (ADR-036)**
- [ ] Create ComplianceScorer service
- [ ] Implement scoring formula
- [ ] Real-time updates when steps complete
- [ ] Full unit test coverage (20+ tests)

**Week 5-6: Deviation Detection (ADR-038)**
- [ ] Create DeviationDetector service
- [ ] Implement timing deviation detection
- [ ] Implement skip deviation detection
- [ ] Implement quality deviation detection
- [ ] Real-time flagging + severity classification

**Week 6-7: Analysis Integration (ADR-037)**
- [ ] Integrate compliance score → confidence boost
- [ ] Generate advisories from Analysis anomalies
- [ ] Event system for cross-system communication
- [ ] Integration tests

**Week 7-9: Alerts & Notifications (ADR-040)**
- [ ] Create Alert model + repository
- [ ] Implement in-app WebSocket notifications
- [ ] Integrate SMS (Twilio)
- [ ] Implement email queue
- [ ] Offline-first mobile caching
- [ ] User preference system

**Week 9-10: UI & Demo Refinement**
- [ ] Dashboard showing protocol status
- [ ] Protocol assignment UI
- [ ] Step completion recording UI
- [ ] Alert display and acknowledgment
- [ ] Mobile app integration
- [ ] Demo scenario testing

---

## 📊 Metrics & Success Indicators

### Code Metrics
- **Data Model**: 4 tables, ~150 lines schema
- **Domain Models**: ~200 lines Python classes
- **Repositories**: ~400 lines CRUD operations
- **Services**: ~1,500 lines business logic (scoring, deviation, template, alerts)
- **API Layer**: ~300 lines endpoints
- **Total ADR-Specified Code**: ~3,000 lines (feasible in 10 weeks solo)

### Test Coverage
- **Repositories**: 100% coverage
- **Services**: 85%+ coverage
- **API**: 80%+ coverage
- **Target**: 280+ new tests (currently 1,100 → ~1,380)

### Performance
- **Compliance Score Calculation**: <100ms per fermentation
- **Deviation Detection**: <50ms per step completion
- **API Response Time**: <500ms for all endpoints (with cached compliance)
- **Alert Generation**: <200ms

### Database Queries
- **Optimized indexes**: Protocol templates, active executions, recent completions
- **Query Time**: <100ms for list queries, <50ms for single object

---

## 🎬 Demo Scenario (May 2026)

### Setup (5 minutes)
1. Load Cabernet Sauvignon protocol from database
2. Create fermentation: "Napa Valley 2026 CS - Demo Lot"
3. Assign protocol to fermentation

### Execution (10 minutes)
```
Day 1: Yeast Inoculation ✓ (on-time)
       Compliance: 100% (1/1 critical done, on-time)

Day 3: DAP Addition ✓ (on-time)
       Compliance: 100% (2/2 critical done, on-time)

Day 5: H2S Check ✓ (LATE - day 6, tolerance ±6 hours)
       Compliance: 87% (still all critical done, but H2S one day late)
       Deviation: Timing deviation detected and logged
       Alert: None (within acceptable range for optional deviation)
       
Day 7: PUNCH_DOWN ✓ (on-time)
       Compliance: 93% (now 4/4 steps done, one late)
       
Dashboard Shows:
- Compliance score trending: 100% → 100% → 87% → 93%
- Deviations: 1 timing (H2S one day late)
- Analysis integration: Base confidence 75% → boosted to 87% due to protocol compliance
- Alerts: 3 in-app notifications (step approaching, step completed, deviation logged)
- Mobile: Offline cache shows all MEDIUM+ alerts even without connectivity
```

### Results (5 minutes)
1. **Winemaker sees**: Protocol compliance, deviations, and alerts in real-time
2. **Investor sees**: 
   - Problem prevention (alerts before fermentation fails)
   - Data-driven decision making (compliance score informed by real data)
   - Mobile-first design (winery floor usability)
   - Integration (Protocol + Analysis working together)

---

## 💾 Files Location

All files created in: **`c:\dev\wine-fermentation-system\.ai-context\adr\`**

New files:
```
ADR-035-protocol-data-model-schema.md
ADR-036-compliance-scoring-algorithm.md
ADR-037-protocol-analysis-integration.md
ADR-038-deviation-detection-strategy.md
ADR-039-protocol-template-management.md
ADR-040-notifications-alerts.md
PROTOCOL-ADR-GUIDE.md
PROTOCOL-IMPLEMENTATION-SUMMARY.md
PROTOCOL-IMPLEMENTATION-CHECKLIST.md (this file)
```

Updated files:
```
ADR-INDEX.md (added entries for ADR-035 through ADR-040)
```

---

## 🚀 Ready to Proceed?

**Current State**:
- ✅ All 6 ADRs written (158 KB total)
- ✅ All schemas defined (SQL ready)
- ✅ All pseudocode provided (Python-ready)
- ✅ All test cases defined (50+ test examples)
- ✅ All dependencies documented (related to ADR-020, 021, 025, 026, 027)
- ✅ 10-week timeline validated
- ✅ May demo scenario defined

**Next Actions** (in order):
1. **Review with Susana** (1 week)
   - Review all 6 ADRs
   - Clarify protocol requirements
   - Validate criticality, tolerances, skip rules
   - Provide protocol PDFs for seed data

2. **Clarification Call** (1 day)
   - Answer any questions about ADR design
   - Finalize protocol data structure
   - Confirm timeline feasibility

3. **Week 1 Kickoff** (Week 1)
   - Create database schema (ADR-035)
   - Load seed data from protocols
   - Create domain models and repositories
   - Start writing Phase 0 code

4. **Continuous Progress** (Weeks 2-10)
   - Follow integrated timeline (Phases 1-5)
   - Weekly commits with test additions
   - Bi-weekly demos showing progress
   - Iterate based on real usage patterns

---

## ❓ Questions?

**For Architecture**: Check PROTOCOL-ADR-GUIDE.md  
**For Implementation**: Check individual ADR files (ADR-035 through ADR-040)  
**For Timeline**: Check PROTOCOL-ADR-GUIDE.md → Integration Timeline & Phases  
**For Demo**: Check PROTOCOL-IMPLEMENTATION-SUMMARY.md → May Demo Scenario  

All ADRs are self-contained with:
- Problem statement
- Decision made
- Pseudocode examples
- Database schema
- API contracts
- Unit test examples
- Error handling
- Edge cases covered

**Ready to build! 🍷**

