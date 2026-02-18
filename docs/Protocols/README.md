# Protocol Engine Documentation Index

**Status**: Master Reference  
**Last Updated**: February 12, 2026  
**Owner**: Protocol Compliance Engine Team

---

## Quick Links

### 🚀 Getting Started
- **Phase 1 Complete**: Domain entities, enums, repositories, DTOs ✅
- **Phase 2 Pending**: REST API endpoints (16 endpoints planned)
- **Phase 3 Pending**: Service layer and compliance scoring

### 📚 Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [PROTOCOL-SEMANTIC-VERSIONING.md](../PROTOCOL-SEMANTIC-VERSIONING.md) | Version strategy, migration paths, backwards compatibility | All developers |
| [PROTOCOL-DATA-READY.md](../PROTOCOL-DATA-READY.md) | Generated protocol data status and structure | Data engineers |
| [PROTOCOL-IMPLEMENTATION-PLAN.md](../PROTOCOL-IMPLEMENTATION-PLAN.md) | Future phases (Phase 2, 3) and implementation roadmap | Architects |

---

## Architecture & ADRs

### Protocol Domain Model (Phase 1 ✅)

**ADR References**: [ADR-035: Protocol Data Model Schema](../../.ai-context/adr/ADR-035-protocol-data-model-schema.md)

**Entities**:
- `FermentationProtocol` - Master template for winery/varietal protocols
- `ProtocolStep` - Ordered steps within a protocol (6 step type categories)
- `ProtocolExecution` - Per-fermentation tracking (4 lifecycle statuses)
- `StepCompletion` - Audit log with skip tracking (5 skip reason types)

**Key Constraints**:
- Unique: (winery_id, varietal_code, version) per protocol
- Unique: (fermentation_id) per execution
- XOR validation: was_skipped XOR completed_at (not both, not neither)
- Score ranges: criticality 0-100, compliance 0-100

**Implementation Status**:
- ✅ 4 domain entities created
- ✅ 3 enums defined (6 step types, 4 execution statuses, 5 skip reasons)
- ✅ 4 async repositories with 38 methods (33 base + 5 pagination)
- ✅ 12 DTOs with validation
- ✅ Database schema via entity definitions
- ✅ 29 unit tests (100% passing)
- ✅ 903/903 system tests passing

### Compliance Scoring (Phase 2)

**ADR References**: [ADR-036: Compliance Scoring Algorithm](../../.ai-context/adr/ADR-036-compliance-scoring-algorithm.md)

**Components** (To Be Implemented):
- Deviation detection from expected vs actual
- Criticality-weighted scoring
- Alert thresholds and notifications
- Anomaly correlation with analysis engine

### Protocol Template Management (Phase 2)

**ADR References**: [ADR-039: Protocol Template Management](../../.ai-context/adr/ADR-039-protocol-template-management.md)

**Features** (To Be Implemented):
- Protocol versioning and activation
- Step reordering and dependency tracking
- Step criticality assignment
- Protocol import/export

---

## File Organization

```
wine-fermentation-system/
├── PROTOCOL-SEMANTIC-VERSIONING.md    # Version strategy guide
├── PROTOCOL-DATA-READY.md              # Data generation status
├── PROTOCOL-IMPLEMENTATION-PLAN.md     # Future phases roadmap
│
├── docs/
│   ├── Protocols/
│   │   ├── README.md                  # This file
│   │   └── (Phase 2 API docs go here)
│   │
│   ├── etl-architecture-refactoring.md
│   └── UML-diagrams/
│
├── src/modules/fermentation/
│   ├── src/domain/
│   │   ├── entities/
│   │   │   ├── fermentation_protocol.py
│   │   │   ├── protocol_step.py
│   │   │   ├── protocol_execution.py
│   │   │   └── step_completion.py
│   │   │
│   │   ├── enums/
│   │   │   ├── step_type.py
│   │   │   ├── protocol_execution_status.py
│   │   │   └── skip_reason.py
│   │   │
│   │   ├── dtos/
│   │   │   ├── protocol_dtos.py
│   │   │   └── __init__.py
│   │   │
│   │   └── repositories/
│   │       ├── *_interface.py (4 interfaces)
│   │       └── __init__.py
│   │
│   ├── src/repository_component/
│   │   ├── *_repository.py (4 implementations)
│   │   └── __init__.py
│   │
│   └── tests/
│       └── unit/
│           └── test_protocol_*.py
│
├── .ai-context/adr/
│   ├── ADR-035-protocol-data-model-schema.md
│   ├── ADR-036-compliance-scoring-algorithm.md
│   ├── ADR-037-protocol-analysis-integration.md
│   ├── ADR-038-deviation-detection-strategy.md
│   ├── ADR-039-protocol-template-management.md
│   ├── ADR-040-notifications-alerts.md
│   └── PROTOCOL-*.md (Quick ref docs)
│
└── .archive/documentation/
    ├── protocol-analysis-phase/
    │   ├── PROTOCOL-ANALYSIS-REAL-DATA.md
    │   ├── PROTOCOL-EXTRACTION-GUIDE.md
    │   ├── PROTOCOL-NEXT-ACTIONS.md
    │   ├── PROTOCOL-READY-TO-CODE.md
    │   └── PROTOCOL-SUSANA-QUESTIONS.md
    │
    └── adr-035-phases/
        ├── ADR-035-PHASE-1-COMPLETE.md
        ├── ADR-035-PHASE-1-IMPLEMENTATION-SUMMARY.md
        └── ADR-035-SESSION-COMPLETE-FINAL-SUMMARY.md
```

---

## Development Roadmap

### Phase 1: Domain Model ✅ COMPLETE

**Duration**: ~2 weeks  
**Status**: DONE (Feb 12, 2026)

**Deliverables**:
- ✅ 4 domain entities with audit fields
- ✅ 3 enums with 11 total values
- ✅ 4 async repositories with 38 methods
- ✅ 12 DTOs with validation functions
- ✅ Database schema via entity imports
- ✅ Comprehensive unit tests (29 tests)
- ✅ Full refactoring suite (pagination, semantic versioning, audit trail)

**Test Results**: 903/903 passing ✅

### Phase 2: REST API Endpoints (Pending)

**Estimated Duration**: 3-4 days  
**Status**: Ready to start

**Scope**:
- 16 REST endpoints (CRUD + list operations)
- Integration with DTOs for type safety
- Error handling and validation
- API documentation (OpenAPI/Swagger)

**Endpoints**:
```
Protocols
├─ POST   /protocols                    # Create protocol
├─ GET    /protocols/{id}               # Get protocol
├─ PATCH  /protocols/{id}               # Update protocol
├─ DELETE /protocols/{id}               # Delete protocol
├─ GET    /protocols                    # List with pagination
└─ PATCH  /protocols/{id}/activate      # Activate version

Protocol Steps
├─ POST   /protocols/{id}/steps         # Add step
├─ PATCH  /protocols/{pid}/steps/{sid}  # Update step
├─ DELETE /protocols/{pid}/steps/{sid}  # Delete step
└─ GET    /protocols/{id}/steps         # List steps (paginated)

Protocol Executions
├─ POST   /fermentations/{id}/execute   # Start execution
├─ PATCH  /executions/{id}              # Update execution status
├─ GET    /executions/{id}              # Get execution details
└─ GET    /executions                   # List (paginated)

Step Completions
├─ POST   /executions/{id}/complete     # Mark step complete
├─ GET    /executions/{id}/completions  # List completions
└─ GET    /completions/{id}             # Get completion details
```

### Phase 3: Service Layer & Compliance (Pending)

**Estimated Duration**: 1-2 weeks  
**Status**: Design complete (ADR-036)

**Scope**:
- Protocol compliance scoring
- Deviation detection
- Skip reason handling
- Alert generation
- Integration with analysis engine

**Components**:
- `ProtocolService` - CRUD + sequencing
- `ComplianceTrackingService` - Scoring and deviation
- `ProtocolAlertService` - Notifications

---

## Key Concepts Reference

### Step Types (6 Categories)

The protocol system uses 6 high-level step type categories instead of 19 specific names. Details go in `ProtocolStep.description`:

| Category | Purpose | Examples |
|----------|---------|----------|
| `INITIALIZATION` | Setup fermentation | Yeast inoculation, temperature prep |
| `MONITORING` | Observe fermentation state | Brix reading, H₂S check |
| `ADDITIONS` | Add materials | Nutrient, DAP, SO₂ additions |
| `CAP_MANAGEMENT` | Manage solids layer | Punch down, pump over |
| `POST_FERMENTATION` | After active fermentation | Settling, racking, filtering |
| `QUALITY_CHECK` | Verify wine quality | Tasting, clarity check |

### Execution Statuses (4 States)

```
NOT_STARTED ──→ ACTIVE ──→ COMPLETED
                  ↓
                PAUSED ──→ COMPLETED
                  ↓
              ABANDONED
```

### Skip Reasons (5 Types)

- `EQUIPMENT_FAILURE` - Equipment malfunction
- `CONDITION_NOT_MET` - Fermentation conditions not right
- `FERMENTATION_ENDED` - Fermentation completed before step
- `FERMENTATION_FAILED` - Unplanned fermentation halt
- `WINEMAKER_DECISION` - Intentional deviation

### Semantic Versioning (X.Y Format)

- **MAJOR (X)**: Fundamental process redesign
- **MINOR (Y)**: Additive improvements or adjustments

Example versions in database:
- `"1.0"` - Original protocol
- `"1.1"` - Added optional step
- `"2.0"` - Complete redesign

See [PROTOCOL-SEMANTIC-VERSIONING.md](../PROTOCOL-SEMANTIC-VERSIONING.md) for detailed version management strategy.

---

## Validation Framework

### DTO-Level Validation

All Protocol DTOs perform validation in `__post_init__()`:

**ProtocolCreate**:
- Version format: regex `^\d+\.\d+$`
- Duration: must be > 0
- Varietal code: 1-4 characters

**StepCreate**:
- Step type: must be one of 6 categories
- Day: must be ≥ 0
- Tolerance: must be ≥ 0
- Criticality: 0-100 range
- Order: must be > 0

**CompletionCreate**:
- Skip reason: required when `was_skipped=True`
- Completed_at: required when `was_skipped=False`
- Valid skip reasons only (5 types)

See [protocol_dtos.py](../src/modules/fermentation/src/domain/dtos/protocol_dtos.py) for implementation.

### Database Constraints

**FermentationProtocol**:
```sql
UNIQUE(winery_id, varietal_code, version)
CHECK(expected_duration_days > 0)
```

**ProtocolStep**:
```sql
UNIQUE(protocol_id, step_order)
CHECK(expected_day >= 0)
CHECK(tolerance_hours >= 0)
CHECK(criticality_score BETWEEN 0 AND 100)
CHECK(duration_minutes > 0)
```

**ProtocolExecution**:
```sql
UNIQUE(fermentation_id)
CHECK(compliance_score BETWEEN 0 AND 100)
```

---

## Repository Methods Reference

### FermentationProtocolRepository

**Base Methods** (33 across all 4 repos):
- `create()`, `get_by_id()`, `update()`, `delete()`
- `list_all()`, `list_by_winery_paginated()`
- `get_by_winery_varietal_version()`, `get_active_by_winery_varietal()`
- `list_by_winery_varietal()`, `deactivate_by_winery_varietal()`

**Pagination**:
- `list_by_winery_paginated(winery_id, page=1, page_size=20)`
  - Returns: `Tuple[List[FermentationProtocol], int]` (items, total_count)
- `list_active_by_winery_paginated(winery_id, page=1, page_size=20)`

### ProtocolStepRepository

**Pagination**:
- `list_by_protocol_paginated(protocol_id, page=1, page_size=20)`
  - Orders by step_order
  - Returns: `Tuple[List[ProtocolStep], int]`

### ProtocolExecutionRepository

**Pagination**:
- `list_by_winery_paginated(winery_id, page=1, page_size=20)`
  - Orders by id DESC (newest first)
  - Returns: `Tuple[List[ProtocolExecution], int]`

### StepCompletionRepository

**Pagination**:
- `list_by_execution_paginated(execution_id, page=1, page_size=20)`
  - Orders by created_at
  - Returns: `Tuple[List[StepCompletion], int]`

---

## Testing

### Unit Tests

**Location**: `tests/unit/test_protocol_*.py`  
**Count**: 29 tests  
**Status**: ✅ All passing

**Coverage**:
- Entity creation and validation
- Enum values
- DTO validation rules
- Repository CRUD operations
- Pagination methods

### System Tests

**Location**: `tests/integration/`  
**Total**: 903 tests across all modules  
**Status**: ✅ All passing

**Protocol Coverage**: 29 unit tests + 874 system/integration tests

---

## Integration Points

### Fermentation Module

Protocol executions track compliance for `Fermentation` entities:

```
Fermentation (existing)
    └─ ProtocolExecution
        ├─ ProtocolStep instances being tracked
        └─ StepCompletion audit trail
```

### Analysis Engine (Future)

Phase 3 will integrate protocol compliance data:

See [ADR-037: Protocol-Analysis Integration](../../.ai-context/adr/ADR-037-protocol-analysis-integration.md)

### Authentication (Shared Module)

User tracking in:
- `FermentationProtocol.created_by_user_id`
- `StepCompletion.verified_by_user_id`
- `StepCompletion.completed_by_user_id`

No FK relationships (follows ADR-020 pattern).

---

## Common Tasks

### Add a New Protocol Type (Winemaker)

```python
# Phase 2 API call (once implemented)
POST /protocols
{
  "winery_id": 1,
  "varietal_code": "CH",
  "protocol_name": "Chardonnay Standard 2024",
  "version": "1.0",
  "expected_duration_days": 30,
  "is_active": false
}
```

Then add steps:
```python
POST /protocols/{protocol_id}/steps
{
  "step_order": 1,
  "step_type": "INITIALIZATION",
  "description": "Cold soak at 10°C for 48 hours",
  "expected_day": 0,
  "tolerance_hours": 4,
  "is_critical": true,
  "criticality_score": 95
}
```

### Activate a Protocol Version

```python
# Deactivate v1.0, activate v1.1
PATCH /protocols/{v1_1_id}/activate
```

New fermentations use v1.1; in-progress fermentations continue with v1.0.

### Start Tracking a Fermentation

```python
POST /fermentations/{fermentation_id}/execute
{
  "protocol_id": 1,
  "winery_id": 1
}
```

Creates `ProtocolExecution` and schedules steps.

### Complete a Step

```python
POST /executions/{execution_id}/complete
{
  "step_id": 5,
  "completed_at": "2026-02-12T14:30:00Z",
  "notes": "H₂S levels normal",
  "is_on_schedule": true,
  "completed_by_user_id": 42
}
```

### Skip a Step

```python
POST /executions/{execution_id}/complete
{
  "step_id": 7,
  "was_skipped": true,
  "skip_reason": "FERMENTATION_ENDED",
  "skip_notes": "Fermentation completed before scheduled step"
}
```

---

## Troubleshooting

### Common Errors

**"Version must be X.Y format"**
- Ensure version string matches regex `^\d+\.\d+$`
- Valid: `"1.0"`, `"1.5"`, `"2.0"`
- Invalid: `"1"`, `"1.0.0"`, `"v1.0"`

**"Duplicate protocol version"**
- Only one version per (winery_id, varietal_code, version) combination
- Solution: Use different version number (e.g., v1.1 instead of v1.0)

**"Step completion XOR violation"**
- Must set either `was_skipped=true` OR `completed_at`, never both
- If skipped: provide `skip_reason`
- If completed: provide `completed_at` timestamp

**"Protocol not active"**
- `is_active=false` prevents new executions
- Solution: `PATCH /protocols/{id}/activate` to enable

---

## Document Maintenance

**Last Updated**: February 12, 2026  
**Version**: 1.0  
**Owner**: Protocol Engine Team  
**Review Frequency**: After each phase completion

### Archive Location

Older documentation (analysis phase, phase completions):
- [.archive/documentation/protocol-analysis-phase/](../../.archive/documentation/protocol-analysis-phase/)
- [.archive/documentation/adr-035-phases/](../../.archive/documentation/adr-035-phases/)

---

## Related Resources

- **Quick Reference**: [PROTOCOL-DEVELOPER-QUICKREF.md](../../.ai-context/adr/PROTOCOL-DEVELOPER-QUICKREF.md)
- **Implementation Guide**: [PROTOCOL-IMPLEMENTATION-CHECKLIST.md](../../.ai-context/adr/PROTOCOL-IMPLEMENTATION-CHECKLIST.md)
- **ADR Index**: [ADR-INDEX.md](../../.ai-context/adr/ADR-INDEX.md)

---

**Next Step**: Begin Phase 2 API development using Phase 1 foundation.
