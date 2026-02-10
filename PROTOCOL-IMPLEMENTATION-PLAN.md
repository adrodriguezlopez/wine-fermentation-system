# Protocol Compliance Engine - Implementation Plan

**Status**: 🔄 Planning Phase  
**Target Start**: [To Be Confirmed]  
**Related ADR**: ADR-021 (Core Engine)  
**Last Updated**: February 7, 2026

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Required ADRs](#required-adrs)
3. [Implementation Phases](#implementation-phases)
4. [Component Breakdown](#component-breakdown)
5. [Integration Points](#integration-points)
6. [Implementation Sequence](#implementation-sequence)
7. [Risks & Mitigations](#risks--mitigations)

---

## System Architecture

### Core Components

```
Protocol Compliance Engine
├── Domain Layer (Phase 0)
│   ├── FermentationProtocol (master template)
│   ├── ProtocolStep (ordered steps)
│   ├── ProtocolExecution (tracking per fermentation)
│   └── StepCompletion (audit log)
│
├── Repository Layer (Phase 1)
│   ├── ProtocolRepository
│   ├── ProtocolExecutionRepository
│   └── StepCompletionRepository
│
├── Service Layer (Phase 2-3)
│   ├── ProtocolService (CRUD, step sequencing)
│   ├── ComplianceTrackingService (scoring, deviation detection)
│   └── ProtocolAlertService (notifications, alerts)
│
├── API Layer (Phase 3)
│   ├── ProtocolRouter
│   └── DTOs (Schemas)
│
└── Integration Points
    ├── Fermentation Module (step tracking)
    ├── Analysis Engine (compliance context)
    └── Notification System (alerts)
```

---

## Required ADRs

### ADR-021 (EXISTING)
**Title**: Fermentation Protocol Compliance Engine  
**Scope**: Core engine, data model, business rules  
**Status**: 📋 Proposed  
**Next Steps**: Validate with Susana, finalize design

---

### ADR-022 (NEW - REQUIRED)
**Title**: Protocol Data Model & Schema Design  
**Scope**: Database schema, entity relationships, constraints  
**Key Decisions**:
- How to store varietal-specific protocols
- Versioning strategy (v1.0, v2.0, etc.)
- Historical tracking of protocol changes
- Relationship between Protocol Steps and Fermentation Samples
- Soft delete support

**Sub-Topics**:
- Protocol hierarchy: Varietal → Version → Steps
- Step uniqueness within protocol (order-based)
- Cascade behavior (delete protocol → delete steps?)
- Audit trail (who created/modified)

---

### ADR-023 (NEW - REQUIRED)
**Title**: Compliance Scoring Algorithm  
**Scope**: How to calculate compliance percentage  
**Key Decisions**:
- **Base Score**: (Completed Steps / Total Steps) × 100
- **Penalties**:
  - Skipped critical step: -10%
  - Step late by 1+ day: -5%
  - Step late by 3+ days: -15%
- **Bonuses** (optional):
  - All steps on time: +5%
  - All critical steps completed: +5%
- **Edge Cases**:
  - Fermentation completed early (8 days instead of 10)
  - Protocol not applicable (fermentation failed day 3)
  - Retroactive step logging

**Formula Example**:
```
Base = (7 / 10) × 100 = 70%
Penalties:
  - 1 skipped critical step: -10%
  - 1 step 2 days late: -5%
Final = 70% - 10% - 5% = 55%
```

---

### ADR-024 (NEW - REQUIRED)
**Title**: Protocol-Analysis Engine Integration  
**Scope**: How Protocol compliance affects Anomaly Detection  
**Key Decisions**:
- **Confidence Adjustment**:
  - If compliance < 80% → Lower anomaly confidence by 15%
  - If critical step skipped → Flag specific risk
- **Context Injection**:
  - Pass compliance_score to AnomalyDetectionService
  - Pass skipped_steps to recommendation engine
  - Use Protocol Step timestamps for context
- **Bidirectional Flow**:
  - Protocol → Analysis (confidence context)
  - Analysis → Protocol (detection of missed H₂S → recommend re-check)

**Example**:
```python
# Protocol says: H₂S check on day 8
# Winemaker skipped it
# Analysis detects: High VA risk
# System combines: "High VA risk + Skipped H₂S check = CRITICAL ALERT"
```

---

### ADR-025 (NEW - REQUIRED)
**Title**: Deviation Detection Strategy  
**Scope**: Real-time detection of protocol deviations  
**Key Decisions**:
- **Detectable Deviations**:
  1. Skipped step (not logged within expected day range)
  2. Out-of-sequence logging (step 5 before step 3)
  3. Schedule violation (step 3 logged on day 10 instead of day 3)
  4. Critical step breach (critical step skipped entirely)
- **Detection Timing**:
  - Real-time (on step log): Check if step is in sequence
  - Periodic (nightly): Check for overdue steps
  - Manual trigger: Winemaker can request deviation report
- **Alert Generation**:
  - INFO: "Step logged (on schedule)"
  - WARNING: "Step logged (2 days late)"
  - ALERT: "Step overdue by 3+ days"
  - CRITICAL: "Critical step skipped"

---

### ADR-026 (NEW - REQUIRED)
**Title**: Template Management & Customization  
**Scope**: How wineries define and manage their protocols  
**Key Decisions**:
- **Scope**:
  - System protocol (read-only default templates)
  - Winery protocol (customized per winery)
  - Protocol versioning (track changes over time)
- **Customization Levels**:
  - Level 0: Use system default (no changes)
  - Level 1: Adjust tolerances (±2 days → ±3 days)
  - Level 2: Add/remove optional steps
  - Level 3: Create custom protocol from scratch
- **Approval Workflow**:
  - Draft → Winery Admin Review → Active
  - Change history tracked
  - Rollback capability

---

### ADR-027 (NEW - REQUIRED)
**Title**: Protocol Notifications & Alerts  
**Scope**: How to notify winemakers about protocol events  
**Key Decisions**:
- **Alert Types**:
  1. **Reminder**: "Next step: H₂S check (tomorrow)"
  2. **Notification**: "Step X overdue (3 days)"
  3. **Alert**: "Critical step skipped: H₂S CHECK"
  4. **Advisory**: "Early fermentation completion (day 8 instead of 10)"
- **Delivery Channels**:
  - In-app notification (dashboard widget)
  - Email digest (daily, weekly)
  - SMS (critical alerts only)
- **Opt-in/Opt-out**:
  - User preferences per notification type
  - Winery-level defaults

---

## Implementation Phases

### Phase 0: Domain Layer ✨ CURRENT
**Duration**: 1-2 weeks  
**Deliverables**:
- ✅ Entity classes (4 entities)
- ✅ Enums (StepType, ComplianceStatus)
- ✅ Value objects (if any)
- ✅ Domain errors/exceptions
- ✅ Repository interfaces
- ✅ Unit tests for entities

**Entities to Create**:
1. `FermentationProtocol` - Master template
2. `ProtocolStep` - Ordered step definition
3. `ProtocolExecution` - Tracks per fermentation
4. `StepCompletion` - Audit log entry

**ADRs to Finalize**:
- ADR-021 (validate with Susana)
- ADR-022 (database schema)
- ADR-026 (template management)

---

### Phase 1: Repository Layer
**Duration**: 1-2 weeks  
**Deliverables**:
- ✅ Repository implementations (3 repos)
- ✅ Database migrations (create tables)
- ✅ Query optimization
- ✅ Integration tests

**Repositories to Create**:
1. `ProtocolRepository` - CRUD operations
2. `ProtocolExecutionRepository` - Execution tracking
3. `StepCompletionRepository` - Step audit log

**Database Tables**:
```sql
fermentation_protocols
protocol_steps
protocol_executions
step_completions
```

**ADRs to Finalize**:
- ADR-022 (validate schema with team)

---

### Phase 2: Service Layer - Core Operations
**Duration**: 2-3 weeks  
**Deliverables**:
- ✅ ProtocolService (Phase 1 of service layer)
- ✅ ComplianceTrackingService (basic scoring)
- ✅ Business logic for step sequencing
- ✅ Service layer tests (50+ tests)

**Services to Create**:
1. `ProtocolService` - Protocol management (CRUD, get_by_varietal, etc.)
2. `ComplianceTrackingService` - Compliance calculation & deviation detection

**Key Methods**:
```python
# ProtocolService
create_protocol(name, varietal, steps)
get_protocol(protocol_id)
update_protocol(protocol_id, updates)
delete_protocol(protocol_id)
get_by_varietal(varietal, winery_id)

# ComplianceTrackingService
calculate_compliance_score(execution_id)
detect_deviations(execution_id)
log_step_completion(execution_id, step_id, notes)
get_overdue_steps(execution_id)
is_step_critical(step_id)
```

**ADRs to Finalize**:
- ADR-023 (compliance scoring algorithm)
- ADR-025 (deviation detection)

---

### Phase 3: API Layer + Integration
**Duration**: 2-3 weeks  
**Deliverables**:
- ✅ ProtocolRouter (FastAPI endpoints)
- ✅ DTOs/Schemas (Pydantic models)
- ✅ ProtocolAlertService (notifications)
- ✅ Integration with Analysis Engine
- ✅ Integration tests + E2E tests

**API Endpoints**:
```
POST   /protocols                    - Create protocol
GET    /protocols/{id}               - Get protocol
PUT    /protocols/{id}               - Update protocol
DELETE /protocols/{id}               - Delete protocol
GET    /protocols/varietal/{var}     - Get by varietal

POST   /fermentations/{id}/protocol/start          - Start execution
POST   /fermentations/{id}/steps/{step_id}/complete - Log step
GET    /fermentations/{id}/protocol/progress       - View progress
GET    /fermentations/{id}/protocol/compliance     - Get score

GET    /fermentations/{id}/protocol/alerts         - Get alerts
GET    /fermentations/{id}/protocol/deviations     - Get deviations
```

**Service Integration**:
```python
# ProtocolAlertService
generate_step_reminder(execution_id, step_id)
generate_overdue_alert(execution_id, step_id)
generate_critical_alert(execution_id, step_id)
send_notification(alert_type, user_id, message)
```

**Analysis Integration**:
```python
# In AnomalyDetectionService
def run_all_detections(fermentation, protocol_context=None):
    if protocol_context:
        compliance_score = protocol_context['compliance_score']
        skipped_critical_steps = protocol_context['skipped_critical_steps']
        
        # Adjust confidence based on protocol compliance
        confidence_multiplier = 1.0 - (100 - compliance_score) / 500
        ...
```

**ADRs to Finalize**:
- ADR-024 (Analysis integration)
- ADR-027 (notifications)

---

### Phase 4: Advanced Features (FUTURE)
**Not in MVP, but planned**:
- Batch operations (create 10 fermentations with same protocol)
- Protocol versioning (handle protocol changes mid-execution)
- Historical analysis (which protocols work best?)
- Machine learning (predict optimal protocol based on conditions)
- Mobile app notifications

---

## Component Breakdown

### Domain Layer (Phase 0)

#### 1. FermentationProtocol
```python
class FermentationProtocol(BaseEntity):
    winery_id: int
    varietal_code: str      # "CS", "CH", "PN"
    varietal_name: str      # "Cabernet Sauvignon"
    protocol_name: str      # "CS-2026-Standard"
    version: int            # v1, v2, v3
    description: str        # Long text
    total_expected_days: int
    is_active: bool
    created_by_user_id: int
    
    # Relationships
    steps: List[ProtocolStep]
    executions: List[ProtocolExecution]
```

#### 2. ProtocolStep
```python
class ProtocolStep(BaseEntity):
    protocol_id: int
    step_order: int         # 1, 2, 3, ...
    step_type: StepType     # Enum
    description: str
    expected_day: int       # What day should this happen?
    duration_hours: int     # How long does it take?
    is_critical: bool       # Penalty if skipped?
    criticality_score: float # 0-100 (for weighted scoring)
    notes: str
    
    # Relationships
    protocol: FermentationProtocol
    completions: List[StepCompletion]
```

#### 3. ProtocolExecution
```python
class ProtocolExecution(BaseEntity):
    fermentation_id: int
    protocol_id: int
    winery_id: int
    start_date: datetime    # When fermentation started
    status: ComplianceStatus
    compliance_score: float # 0-100%
    completed_steps: int    # Count of completed steps
    notes: str
    
    # Relationships
    protocol: FermentationProtocol
    fermentation: Fermentation
    completions: List[StepCompletion]
```

#### 4. StepCompletion
```python
class StepCompletion(BaseEntity):
    execution_id: int
    step_id: int
    completed_at: datetime
    notes: str
    on_schedule: bool       # Completed within expected day + tolerance?
    verified_by_user_id: int
    
    # Relationships
    execution: ProtocolExecution
    step: ProtocolStep
    user: User
```

#### Enums
```python
class StepType(str, Enum):
    YEAST_COUNT = "YEAST_COUNT"
    DAP_ADDITION = "DAP_ADDITION"
    H2S_CHECK = "H2S_CHECK"
    PUNCHING_DOWN = "PUNCHING_DOWN"
    TEMPERATURE_CHECK = "TEMPERATURE_CHECK"
    DENSITY_MEASUREMENT = "DENSITY_MEASUREMENT"
    NUTRIENT_ADDITION = "NUTRIENT_ADDITION"
    RELEASE_CO2 = "RELEASE_CO2"
    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    CATA_TASTING = "CATA_TASTING"

class ComplianceStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ON_SCHEDULE = "ON_SCHEDULE"
    DELAYED = "DELAYED"
    SKIPPED = "SKIPPED"
    COMPLETED = "COMPLETED"
    DEVIATION_DETECTED = "DEVIATION_DETECTED"
```

---

### Repository Layer (Phase 1)

#### ProtocolRepository
```python
class IProtocolRepository(Protocol):
    async def create(protocol: FermentationProtocol) -> FermentationProtocol
    async def get_by_id(id: int, winery_id: int) -> FermentationProtocol
    async def get_by_varietal(varietal: str, winery_id: int) -> FermentationProtocol
    async def list_by_winery(winery_id: int) -> List[FermentationProtocol]
    async def list_active(winery_id: int) -> List[FermentationProtocol]
    async def update(id: int, updates: dict) -> FermentationProtocol
    async def delete(id: int, winery_id: int) -> None
```

#### ProtocolExecutionRepository
```python
class IProtocolExecutionRepository(Protocol):
    async def create(execution: ProtocolExecution) -> ProtocolExecution
    async def get_by_id(id: int, winery_id: int) -> ProtocolExecution
    async def get_by_fermentation(ferm_id: int, winery_id: int) -> ProtocolExecution
    async def update_compliance_score(id: int, score: float) -> ProtocolExecution
    async def list_by_winery(winery_id: int) -> List[ProtocolExecution]
    async def list_active(winery_id: int) -> List[ProtocolExecution]
```

#### StepCompletionRepository
```python
class IStepCompletionRepository(Protocol):
    async def create(completion: StepCompletion) -> StepCompletion
    async def get_by_execution(execution_id: int) -> List[StepCompletion]
    async def get_by_step(step_id: int) -> List[StepCompletion]
    async def list_pending(execution_id: int) -> List[ProtocolStep]
    async def get_latest_completion(step_id: int) -> StepCompletion
```

---

### Service Layer (Phase 2-3)

#### ProtocolService (Phase 1-2)
**Responsibilities**: Protocol CRUD, step management, sequencing

#### ComplianceTrackingService (Phase 2-3)
**Responsibilities**: Scoring, deviation detection, step logging

#### ProtocolAlertService (Phase 3)
**Responsibilities**: Notifications, reminders, alerts

---

## Integration Points

### 1. Fermentation Module Integration
**Connection**: ProtocolExecution ← → Fermentation

```python
# When fermentation starts
fermentation_service.create_fermentation(...)
protocol_service.start_execution(fermentation_id, protocol_id)

# When sample added
sample_service.create_sample(...)
protocol_service.check_step_timing(execution_id, sample_type)  # Suggestion

# When fermentation completes
fermentation_service.complete_fermentation(...)
compliance_service.calculate_final_score(execution_id)
```

### 2. Analysis Engine Integration (ADR-024)
**Connection**: Compliance Score → Anomaly Confidence

```python
# In AnomalyDetectionService
def run_detection_for_sample(sample, fermentation):
    protocol_context = await protocol_service.get_execution_context(fermentation.id)
    
    anomalies = []
    for detector in detectors:
        anomaly = detector.detect(sample, fermentation)
        
        if protocol_context:
            # Adjust confidence based on protocol compliance
            anomaly.confidence *= (protocol_context.compliance_score / 100)
            
            # Flag skipped critical steps
            if 'H2S_CHECK' in protocol_context.skipped_critical_steps:
                anomaly.flag_as_contextual_risk("H2S check skipped")
        
        anomalies.append(anomaly)
    
    return anomalies
```

### 3. Notification System Integration
**Connection**: Protocol Events → Notifications

```python
# When step becomes overdue
if step_overdue:
    alert_service.generate_alert(
        type="STEP_OVERDUE",
        fermentation_id=execution.fermentation_id,
        step=step,
        days_overdue=days_late
    )
    notify_service.send_to_user(user_id, alert)
```

---

## Implementation Sequence

### Week 1: Domain Layer (Phase 0)
1. Finalize ADR-021, ADR-022, ADR-026
2. Create entity classes (4 files)
3. Create enums + exceptions
4. Create repository interfaces
5. Write unit tests (20+ tests)
6. Code review + feedback

### Week 2: Domain + Early Repository
1. Finalize ADR-023, ADR-025
2. Implement ProtocolRepository
3. Write integration tests
4. Create database migrations
5. Test with sample data

### Week 3-4: Complete Repository + Service
1. Implement remaining repositories
2. Create ProtocolService + basic ComplianceTrackingService
3. Write service tests (30+ tests)
4. Integrate with Fermentation module

### Week 5: Service Completion + Analysis Integration
1. Complete ComplianceTrackingService
2. Implement compliance scoring algorithm (ADR-023)
3. Implement deviation detection (ADR-025)
4. Integrate with Analysis Engine (ADR-024)
5. Cross-module tests

### Week 6: API Layer + Notifications
1. Finalize ADR-024, ADR-027
2. Create ProtocolRouter + DTOs
3. Implement ProtocolAlertService
4. E2E tests
5. Documentation

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Compliance scoring algorithm unclear | HIGH | HIGH | Validate with Susana before Phase 2 coding |
| Protocol template design too rigid | MEDIUM | HIGH | Allow versioning + customization (ADR-026) |
| Analysis integration too complex | MEDIUM | MEDIUM | Design integration API first (ADR-024) |
| Notification system not ready | MEDIUM | LOW | Use in-app notifications as fallback |
| Performance issues with compliance calc | LOW | MEDIUM | Test with 1000+ steps; optimize queries |
| Missed edge cases in deviation logic | MEDIUM | HIGH | Comprehensive test suite + Susana review |

---

## Success Criteria

**Phase 0 (Domain)**:
- ✅ All 4 entities defined and tested
- ✅ All ADRs reviewed and approved
- ✅ Susana validates domain model

**Phase 1 (Repository)**:
- ✅ All tables created + migrated
- ✅ All queries optimized (<100ms)
- ✅ 95%+ test coverage

**Phase 2 (Service)**:
- ✅ Compliance scoring matches ADR-023
- ✅ Deviation detection catches all edge cases
- ✅ Service tests pass

**Phase 3 (API + Integration)**:
- ✅ All endpoints working
- ✅ Analysis integration validated
- ✅ E2E tests pass
- ✅ Winemaker can use Protocol Compliance features

---

## Questions for Susana

Before starting implementation:

1. **Tolerance Levels**: Are ±2 days the right tolerance for all steps, or does it vary?
2. **Critical Steps**: Which steps are truly critical? (H2S_CHECK, YEAST_COUNT, etc.)
3. **Protocol Versions**: Do protocols change season-to-season? How do we handle that?
4. **Step Flexibility**: Can steps be done in different order, or must they be strict sequence?
5. **Skip Rules**: Under what conditions can a step be legitimately skipped?
6. **Compliance Weighting**: Should critical steps count more in the score (weighted)?
7. **Alerts**: What notification frequency would be helpful without being annoying?

---

## Next Steps

1. **Review & Approve**: Team reviews this plan
2. **Finalize ADRs**: ADR-021 through ADR-027
3. **Susana Interview**: Validate domain model + scoring algorithm
4. **Timeline Estimate**: Get team capacity estimates
5. **Start Phase 0**: Begin domain layer implementation

**Decision Point**: Should we proceed with Phase 0 (Domain) first?

