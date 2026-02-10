# Protocol Domain Model Guide

> **Reference**: ADR-035 - Protocol Engine Architecture

## Domain Entities Overview

### FermentationProtocol (Master Template)
**Purpose**: Define a reusable fermentation protocol for a specific varietal at a specific winery.

**Key Attributes**:
```
- id: Integer (auto-generated PK)
- winery_id: Integer (FK to wineries) - which winery owns this protocol
- created_by_user_id: Integer - audit trail (no FK to avoid cross-module dependencies)
- varietal_code: String(10) - short code like "PN", "CH", "CS"
- varietal_name: String(100) - full name like "Pinot Noir"
- color: String(10) - RED, WHITE, or ROSÉ
- protocol_name: String(200) - human-readable name like "PN-2021-Standard"
- version: String(10) - semantic version "1.0", "2.0", etc.
- description: Optional[Text] - detailed protocol description
- expected_duration_days: Integer - typical fermentation duration
- is_active: Boolean - version control flag
- created_at: DateTime - timestamp
- updated_at: DateTime - last modification time
```

**Unique Constraints**:
- (winery_id, varietal_code, version) - only one version of a protocol per varietal per winery

**Check Constraints**:
- expected_duration_days > 0
- color IN ('RED', 'WHITE', 'ROSÉ')

**Relationships**:
- `steps: List[ProtocolStep]` - one-to-many, cascade delete
- `executions: List[ProtocolExecution]` - one-to-many, cascade delete

**Example Usage**:
```python
protocol = FermentationProtocol(
    winery_id=1,
    created_by_user_id=42,
    varietal_code="PN",
    varietal_name="Pinot Noir",
    color="RED",
    protocol_name="PN-2021-Standard",
    version="1.0",
    expected_duration_days=21,
    is_active=True,
    description="Standard protocol for Pinot Noir, optimized for 2021 vintage"
)
```

---

### ProtocolStep (Step Definition)
**Purpose**: Define an individual step within a protocol with timing and criticality information.

**Key Attributes**:
```
- id: Integer (auto-generated PK)
- protocol_id: Integer (FK to fermentation_protocols)
- depends_on_step_id: Optional[Integer] (self-referential FK for dependencies)
- step_order: Integer - sequence position (1, 2, 3, ...)
- step_type: StepType enum - DAP_ADD, YEAST_INOCULATION, TEMPERATURE_CHECK, etc.
- description: Text - what needs to be done
- expected_day: Integer - which day of fermentation (0 = crush day)
- tolerance_hours: Integer - acceptable ±N hours window
- duration_minutes: Integer - how long the step takes
- is_critical: Boolean - critical vs optional
- criticality_score: Float - 0-100 importance rating
- can_repeat_daily: Boolean - can be done multiple times
- notes: Optional[Text] - additional guidance
- created_at: DateTime
```

**Unique Constraints**:
- (protocol_id, step_order) - unique order within protocol

**Check Constraints**:
- expected_day >= 0
- tolerance_hours >= 0
- duration_minutes >= 0
- criticality_score BETWEEN 0 AND 100

**Relationships**:
- `protocol: FermentationProtocol` - many-to-one
- `dependency: Optional[ProtocolStep]` - self-referential, optional
- `completions: List[StepCompletion]` - one-to-many audit trail

**Example Usage**:
```python
step = ProtocolStep(
    protocol_id=1,
    step_order=1,
    step_type=StepType.YEAST_INOCULATION,
    description="Add yeast at 22°C",
    expected_day=0,  # crush day
    tolerance_hours=4,
    duration_minutes=120,
    is_critical=True,
    criticality_score=95,
    can_repeat_daily=False,
    notes="Use dry yeast from refrigerated stock"
)

# Step that depends on another
step2 = ProtocolStep(
    protocol_id=1,
    step_order=2,
    depends_on_step_id=step.id,  # depends on step 1
    step_type=StepType.TEMPERATURE_CHECK,
    description="Check temperature stabilized",
    expected_day=1,
    tolerance_hours=12
    # ...
)
```

---

### ProtocolExecution (Execution Tracking)
**Purpose**: Track how a specific fermentation adheres to a protocol template.

**Key Attributes**:
```
- id: Integer (auto-generated PK)
- fermentation_id: Integer (FK to fermentations) - UNIQUE 1:1 mapping
- protocol_id: Integer (FK to fermentation_protocols)
- winery_id: Integer (FK to wineries) - denormalized for querying
- start_date: DateTime - when fermentation started
- status: ProtocolExecutionStatus - NOT_STARTED, ACTIVE, COMPLETED, ABANDONED
- compliance_score: Float - 0-100% adherence rating
- completed_steps: Integer - count of completed steps
- skipped_critical_steps: Integer - count of critical steps skipped
- notes: Optional[Text] - execution notes or deviations
- created_at: DateTime - when execution started tracking
- completed_at: Optional[DateTime] - when execution finished
```

**Unique Constraints**:
- (fermentation_id) - one execution per fermentation

**Check Constraints**:
- compliance_score BETWEEN 0 AND 100

**Relationships**:
- `protocol: FermentationProtocol` - many-to-one
- `completions: List[StepCompletion]` - one-to-many, cascade delete

**Example Usage**:
```python
execution = ProtocolExecution(
    fermentation_id=123,  # specific fermentation
    protocol_id=1,        # using PN-2021-Standard protocol
    winery_id=1,
    start_date=datetime(2026, 2, 9, 10, 30),
    status=ProtocolExecutionStatus.ACTIVE,
    compliance_score=92.5,
    completed_steps=8,
    skipped_critical_steps=0,
    notes="Running normally, one day ahead of schedule"
)
```

---

### StepCompletion (Audit Trail)
**Purpose**: Create detailed record of when/how each protocol step was completed.

**Key Attributes**:
```
- id: Integer (auto-generated PK)
- execution_id: Integer (FK to protocol_executions)
- step_id: Integer (FK to protocol_steps)
- verified_by_user_id: Optional[Integer] - who verified (no FK to avoid cross-module dep)
- completed_at: Optional[DateTime] - when step was actually completed
- notes: Optional[Text] - what was observed
- is_on_schedule: Optional[Boolean] - within tolerance window?
- days_late: Integer - 0 if on-time, >0 if late
- was_skipped: Boolean - step was skipped?
- skip_reason: Optional[SkipReason] - why was it skipped?
- skip_notes: Optional[Text] - detailed justification
- created_at: DateTime - when record was created
```

**Unique Constraints**:
- (execution_id, step_id, completed_at) - allows multiple completions per step

**Check Constraints**:
- (was_skipped = true AND skip_reason IS NOT NULL) OR was_skipped = false

**Relationships**:
- `execution: ProtocolExecution` - many-to-one
- `step: ProtocolStep` - many-to-one

**Example Usage**:
```python
# Step completed on time
completion = StepCompletion(
    execution_id=1,
    step_id=1,
    verified_by_user_id=42,
    completed_at=datetime(2026, 2, 9, 10, 45),
    notes="Yeast rehydrated properly, added to must",
    is_on_schedule=True,
    days_late=0,
    was_skipped=False
)

# Step skipped with reason
skip_completion = StepCompletion(
    execution_id=1,
    step_id=2,
    completed_at=None,
    is_on_schedule=None,
    was_skipped=True,
    skip_reason=SkipReason.WEATHER,
    skip_notes="Temperature too cold, will retry when warmer",
    created_at=datetime.now()
)
```

---

## Domain Enums

### StepType (14 step types)
```python
class StepType(str, Enum):
    # Temperature management
    TEMPERATURE_CHECK = "TEMPERATURE_CHECK"
    COOLING = "COOLING"
    HEATING = "HEATING"
    
    # Nutrient additions
    DAP_ADD = "DAP_ADD"  # Di-ammonium phosphate
    NUTRIENT_ADD = "NUTRIENT_ADD"
    
    # Yeast management
    YEAST_INOCULATION = "YEAST_INOCULATION"
    YEAST_REARING = "YEAST_REARING"
    
    # Monitoring
    SG_READING = "SG_READING"  # Specific gravity
    BRIX_READING = "BRIX_READING"
    pH_READING = "pH_READING"
    TA_READING = "TA_READING"  # Titratable acidity
    
    # Process steps
    PUNCH_DOWN = "PUNCH_DOWN"
    RACK_TRANSFER = "RACK_TRANSFER"
    FILTER = "FILTER"
```

### ProtocolExecutionStatus (4 statuses)
```python
class ProtocolExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"  # Template assigned, not started
    ACTIVE = "ACTIVE"            # Currently tracking steps
    COMPLETED = "COMPLETED"      # Fermentation finished
    ABANDONED = "ABANDONED"      # Protocol abandoned mid-fermentation
```

### SkipReason (5 skip reasons)
```python
class SkipReason(str, Enum):
    WEATHER = "WEATHER"                    # Weather prevented step
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"  # Equipment broken
    SUPPLY_SHORTAGE = "SUPPLY_SHORTAGE"    # Missing materials
    TIME_CONSTRAINT = "TIME_CONSTRAINT"    # Not enough time
    FERMENTATION_STATE = "FERMENTATION_STATE"  # Wrong fermentation state
```

---

## Relationships Diagram

```
FermentationProtocol (1)
    ├── has many ProtocolStep (protocol_id FK)
    │       ├── self-references ProtocolStep (depends_on_step_id FK)
    │       └── has many StepCompletion (step_id FK)
    │
    └── has many ProtocolExecution (protocol_id FK)
            └── has many StepCompletion (execution_id FK)

ProtocolExecution
    ├── references FermentationProtocol (1:N)
    ├── has many StepCompletion (1:N, cascade delete)
    └── 1:1 mapping to Fermentation (fermentation_id UNIQUE)

StepCompletion
    ├── references ProtocolExecution (execution_id FK)
    └── references ProtocolStep (step_id FK)
```

---

## Data Flow Example

### Creating and Executing a Protocol

```python
# 1. Create protocol template
protocol = await protocol_repo.create(
    winery_id=1,
    varietal_code="PN",
    varietal_name="Pinot Noir",
    color="RED",
    protocol_name="PN-2021-Standard",
    version="1.0",
    expected_duration_days=21,
    created_by=user_id
)

# 2. Add steps to protocol
step1 = await step_repo.create(
    protocol_id=protocol.id,
    step_order=1,
    step_type=StepType.YEAST_INOCULATION,
    expected_day=0,
    # ... other fields
)

step2 = await step_repo.create(
    protocol_id=protocol.id,
    step_order=2,
    depends_on_step_id=step1.id,
    step_type=StepType.TEMPERATURE_CHECK,
    expected_day=1,
    # ... other fields
)

# 3. Start fermentation with protocol
fermentation = ... # create fermentation
execution = await execution_repo.create(
    fermentation_id=fermentation.id,
    protocol_id=protocol.id,
    winery_id=1,
    start_date=datetime.now(),
    status=ProtocolExecutionStatus.ACTIVE
)

# 4. Record step completions
completion1 = await completion_repo.record_completion(
    execution_id=execution.id,
    step_id=step1.id,
    verified_by_user_id=user_id,
    completed_at=datetime.now(),
    notes="Yeast rehydrated and added"
)

# 5. Query execution compliance
execution = await execution_repo.get_by_fermentation(fermentation.id)
print(f"Compliance: {execution.compliance_score}%")
print(f"Steps completed: {execution.completed_steps}")
```

---

## Testing Strategies

### Unit Tests
- Entity instantiation with valid/invalid data
- Constraint validation
- Enum value validation

### Integration Tests
- Complex workflows (create protocol → add steps → execute → track completion)
- Constraint enforcement at database level
- Relationship cascades
- Query filters and sorting

### Key Test Scenarios
1. **Protocol creation with unique constraints** - one version per varietal per winery
2. **Step dependencies** - self-referential relationships work correctly
3. **Execution tracking** - compliance score updates correctly
4. **Completion audit trail** - allows multiple completions per step
5. **Skip validation** - skip_reason required when was_skipped=true

---

**Document Version**: 1.0  
**Last Updated**: February 9, 2026  
**Status**: Complete with all 29 tests passing
