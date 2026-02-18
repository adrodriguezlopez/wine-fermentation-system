# ✅ Protocol Structure Ready to Code - Complete Analysis

**Status**: YES - You have EVERYTHING needed to start coding the database layer  
**Date**: February 9, 2026

---

## 🎯 What You Have

### ✅ Complete Data Model (ADR-035)

**4 Core Entities** with full details:

1. **FermentationProtocol** (Master Template)
   - Fields: ID, winery_id, varietal_code, varietal_name, version, protocol_name, description, color, expected_duration_days, is_active, created_by_user_id, timestamps
   - Relationships: Many ProtocolSteps, Many ProtocolExecutions
   - Constraints: Unique(winery_id, varietal_code, version)

2. **ProtocolStep** (Ordered Steps)
   - Fields: ID, protocol_id, step_order, step_type (enum), description, expected_day, tolerance_hours, duration_minutes, is_critical, criticality_score, depends_on_step_id, can_repeat_daily, notes
   - Relationships: One FermentationProtocol, Many StepCompletions
   - Constraints: Unique(protocol_id, step_order)
   - Step types: 17 enums (YEAST_INOCULATION, H2S_CHECK, BRIX_READING, etc.)

3. **ProtocolExecution** (Per-Fermentation Tracking)
   - Fields: ID, fermentation_id, protocol_id, winery_id, start_date, status (enum), compliance_score, completed_steps, skipped_critical_steps, notes, timestamps
   - Relationships: One Fermentation, One FermentationProtocol, Many StepCompletions
   - Status values: NOT_STARTED, ACTIVE, PAUSED, COMPLETED, ABANDONED
   - Constraints: Unique(fermentation_id)

4. **StepCompletion** (Audit Log)
   - Fields: ID, execution_id, step_id, completed_at, notes, is_on_schedule, days_late, was_skipped, skip_reason (enum), skip_notes, verified_by_user_id, created_at
   - Relationships: One ProtocolExecution, One ProtocolStep, One User
   - Skip reasons: EQUIPMENT_FAILURE, CONDITION_NOT_MET, FERMENTATION_ENDED, FERMENTATION_FAILED, WINEMAKER_DECISION, REPLACED_BY_ALTERNATIVE, OTHER

### ✅ Complete SQL Schema

**4 Tables with Indexes**:
```
fermentation_protocols (7 columns, 1 unique constraint, 1 check)
protocol_steps (11 columns, 2 unique constraints, 3 checks)
protocol_executions (10 columns, 1 unique constraint, 1 check)
step_completions (10 columns, 1 unique constraint, 1 check)
```

**Indexes** for performance:
- idx_protocols_winery_active
- idx_protocols_varietal
- idx_executions_fermentation
- idx_executions_status
- idx_completions_execution
- idx_completions_completed_at

### ✅ Complete Enum Definitions

- **StepType**: 17 enums for winery operations
- **ProtocolExecutionStatus**: 5 enums for lifecycle
- **SkipReason**: 7 enums for deviation tracking

### ✅ Integration Points Defined

- **Links to Fermentation**: ProtocolExecution.fermentation_id → Fermentation.id
- **Links to User**: StepCompletion.verified_by_user_id → User.id
- **Links to Winery**: FermentationProtocol.winery_id → Winery.id (multi-tenancy)

---

## 🚀 What's Missing (To Start Coding)

### Category 1: Data (Needed This Week)
**Status**: 3 Priority PDFs need extraction

```
BEFORE you can load data:
├─ Extract Pinot Noir protocol from PDF
├─ Extract Chardonnay protocol from PDF
├─ Extract Cabernet Sauvignon protocol from PDF
└─ Convert to JSON/CSV format (template in PROTOCOL-EXTRACTION-GUIDE.md)
```

**Why**: You need actual protocol steps to seed the database. Don't code with fake data.

**Timeline**: 2-3 days (user extracts manually using provided guide)

**Deliverable**: 3 JSON files with real Pinot/Chardonnay/Cabernet protocols

### Category 2: Python Domain Models (Can code now)
**Status**: Can be created immediately from ADR-035

```python
# YOU NEED TO CREATE:
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

class FermentationProtocol(BaseEntity):
    # 13 fields with proper SQLAlchemy types and relationships
    pass

class ProtocolStep(BaseEntity):
    # 11 fields with enums and dependencies
    pass

class ProtocolExecution(BaseEntity):
    # 10 fields with status tracking
    pass

class StepCompletion(BaseEntity):
    # 10 fields with audit trail
    pass

# Plus 3 Enums:
class StepType(str, Enum):
    # 17 values
    pass

class ProtocolExecutionStatus(str, Enum):
    # 5 values
    pass

class SkipReason(str, Enum):
    # 7 values
    pass
```

**Timeline**: 1-2 hours to write, follows exact same pattern as existing `fermentation.py`

### Category 3: Repositories (Can code after models)
**Status**: Clear pattern from existing codebase

```python
# YOU NEED TO CREATE:
class FermentationProtocolRepository(IFermentationProtocolRepository):
    # Standard CRUD: create, read, list, update, delete
    # Custom: get_by_winery_varietal_version, get_active_protocols, etc.

class ProtocolStepRepository(IProtocolStepRepository):
    # Standard CRUD
    # Custom: get_steps_by_protocol, get_by_order, etc.

class ProtocolExecutionRepository(IProtocolExecutionRepository):
    # Standard CRUD
    # Custom: get_by_fermentation, get_by_status, etc.

class StepCompletionRepository(IStepCompletionRepository):
    # Standard CRUD
    # Custom: get_by_execution, get_by_step, record_completion, etc.
```

**Timeline**: 2-3 hours (copy existing patterns)

### Category 4: Service Layer (Depends on repositories)
**Status**: Defined in ADR-036, ADR-037, ADR-038

```python
# YOU NEED TO CREATE:
class ProtocolService:
    # assign_protocol_to_fermentation(fermentation_id, protocol_id)
    # start_protocol_execution(fermentation_id)
    # complete_step(execution_id, step_id, notes)
    # skip_step(execution_id, step_id, skip_reason)
    # get_compliance_score(execution_id)  # Calls ADR-036

class ProtocolComplianceService:
    # calculate_compliance_score(execution_id)  # From ADR-036
    # detect_deviations(execution_id)  # From ADR-038

class ProtocolNotificationService:
    # generate_alerts(execution_id)  # From ADR-040
    # check_late_steps(execution_id)
```

**Timeline**: 4-5 hours (implementation logic, formulas)

---

## 📋 Step-by-Step Coding Plan (Starting Now)

### PHASE 1: Domain Models (1-2 Hours)

**File**: `src/modules/fermentation/src/domain/entities/protocol_protocol.py`
```python
class FermentationProtocol(BaseEntity):
    __tablename__ = "fermentation_protocols"
    # Copy structure from ADR-035, follow existing fermentation.py pattern
```

**File**: `src/modules/fermentation/src/domain/entities/protocol_step.py`
```python
class ProtocolStep(BaseEntity):
    __tablename__ = "protocol_steps"
    # 11 fields, step_type as enum
```

**File**: `src/modules/fermentation/src/domain/entities/protocol_execution.py`
```python
class ProtocolExecution(BaseEntity):
    __tablename__ = "protocol_executions"
    # Link to Fermentation, status as enum
```

**File**: `src/modules/fermentation/src/domain/entities/step_completion.py`
```python
class StepCompletion(BaseEntity):
    __tablename__ = "step_completions"
    # Audit trail, skip_reason as enum
```

**File**: `src/modules/fermentation/src/domain/enums/step_type.py`
```python
class StepType(str, Enum):
    YEAST_INOCULATION = "YEAST_INOCULATION"
    H2S_CHECK = "H2S_CHECK"
    # ... all 17 types
```

**File**: `src/modules/fermentation/src/domain/enums/protocol_execution_status.py`
```python
class ProtocolExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    # ... all 5 statuses
```

**File**: `src/modules/fermentation/src/domain/enums/skip_reason.py`
```python
class SkipReason(str, Enum):
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    # ... all 7 reasons
```

### PHASE 2: Repositories (2-3 Hours)

**File**: `src/modules/fermentation/src/domain/repositories/fermentation_protocol_repository_interface.py`
```python
class IFermentationProtocolRepository(ABC):
    @abstractmethod
    async def create(self, protocol: FermentationProtocol) -> FermentationProtocol:
        pass
    # ... standard CRUD + custom queries
```

**File**: `src/modules/fermentation/src/repository_component/fermentation_protocol_repository.py`
```python
class FermentationProtocolRepository(IFermentationProtocolRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create(self, protocol: FermentationProtocol) -> FermentationProtocol:
        # Implementation using sqlalchemy
```

(Repeat for ProtocolStep, ProtocolExecution, StepCompletion)

### PHASE 3: Services (4-5 Hours)

**File**: `src/modules/fermentation/src/service_component/protocol_service.py`
```python
class ProtocolService:
    def __init__(
        self,
        protocol_repo: IFermentationProtocolRepository,
        execution_repo: IProtocolExecutionRepository,
        step_completion_repo: IStepCompletionRepository,
    ):
        # Dependency injection
    
    async def assign_protocol_to_fermentation(
        self, fermentation_id: int, protocol_id: int
    ) -> ProtocolExecution:
        # Create ProtocolExecution record
        # Set status = NOT_STARTED
        # Calculate initial compliance_score = 0
```

### PHASE 4: Database Migration (1 Hour)

**File**: `migrations/versions/xxx_create_protocol_tables.py`
```python
def upgrade():
    op.create_table('fermentation_protocols', ...)
    op.create_table('protocol_steps', ...)
    op.create_table('protocol_executions', ...)
    op.create_table('step_completions', ...)
    op.create_index(...)  # Add 6 indexes

def downgrade():
    op.drop_table('step_completions')
    # ... cascade deletes
```

### PHASE 5: Seed Data (When Extractions Ready)

**File**: `seeds/protocol_seed_data.py`
```python
# After extracting Pinot/Chardonnay/Cabernet:
async def seed_protocols(db_session: AsyncSession):
    # Load JSON files
    # Create FermentationProtocol + ProtocolStep records
    # Commit to database
```

---

## 🎯 What You CAN Code Right Now (Today)

### ✅ TODAY: Entities & Enums (No Data Needed)

Create these files - **no PDFs required, no data required**:

1. **Protocol domain entities** (4 files)
   - FermentationProtocol, ProtocolStep, ProtocolExecution, StepCompletion
   - Copy exact schema from ADR-035, follow fermentation.py pattern
   - Estimated: 45 minutes

2. **Protocol enums** (3 files)
   - StepType (17 values), ProtocolExecutionStatus (5 values), SkipReason (7 values)
   - Copy exact values from ADR-035
   - Estimated: 15 minutes

**Total time**: ~1 hour, produces production-ready code

### ✅ TOMORROW: Repositories (No Data Needed)

Create repository layer using exact pattern from existing code:

1. **Repository interfaces** (4 files)
   - Standard CRUD + custom queries
   - Estimated: 1 hour

2. **Repository implementations** (4 files)
   - SQLAlchemy patterns, async/await
   - Estimated: 2 hours

**Total time**: ~3 hours, produces production-ready code

### ⏳ NEXT WEEK: Services (Partial - No Data)

Create service layer for protocol logic:

1. **ProtocolService**
   - assign_protocol_to_fermentation()
   - start_protocol_execution()
   - complete_step(), skip_step()
   - Estimated: 2 hours (logic, but formula from ADR-036)

2. **ProtocolComplianceService**
   - calculate_compliance_score() - formula in ADR-036
   - detect_deviations() - logic in ADR-038
   - Estimated: 2 hours (but needs ADR-036 scoring formula)

3. **Database migration**
   - Create 4 tables, add 6 indexes
   - Estimated: 1 hour

**Total time**: ~5 hours, produces working database layer

### ⏳ WHEN EXTRACTIONS READY: Seed Data

After you extract Pinot/Chardonnay/Cabernet protocols:

1. **Seed script**
   - Load JSON → Database
   - Create ProtocolStep records for each step
   - Estimated: 1 hour

2. **Integration tests**
   - Verify relationships work
   - Test compliance calculation
   - Estimated: 2 hours

**Total time**: ~3 hours, produces seed data + tests

---

## 📊 CODING ROADMAP

```
TODAY (Feb 9):
├─ [ ] Create 4 entity files (Protocol, Step, Execution, Completion)
├─ [ ] Create 3 enum files (StepType, Status, SkipReason)
└─ Result: Domain layer complete (ready to commit)

TOMORROW (Feb 10):
├─ [ ] Create 4 repository interface files
├─ [ ] Create 4 repository implementation files
└─ Result: Repository layer complete (ready to commit)

WEDNESDAY (Feb 11):
├─ [ ] Create ProtocolService (basic CRUD + lifecycle)
├─ [ ] Create database migration
├─ [ ] Run migration locally
└─ Result: Database tables live (ready for data)

THURSDAY (Feb 12):
├─ [ ] Extract Pinot Noir from PDF (your task, not code)
├─ [ ] Extract Chardonnay from PDF (your task, not code)
├─ [ ] Extract Cabernet from PDF (your task, not code)
└─ Result: 3 JSON files with real protocol steps

FRIDAY (Feb 13):
├─ [ ] Create seed script (load JSON → DB)
├─ [ ] Run seed script
├─ [ ] Write integration tests
└─ Result: Live protocols in database (ready for features)

WEEK 2 (Feb 16+):
├─ [ ] ProtocolComplianceService (scoring formula from ADR-036)
├─ [ ] ProtocolNotificationService (alerts from ADR-040)
├─ [ ] API endpoints to query protocols
└─ Result: Full Protocol Engine ready
```

---

## 🔍 Comparison with Existing Code

Your existing `Fermentation` entity has:

```python
class Fermentation(BaseEntity):
    __tablename__ = "fermentations"
    fermented_by_user_id: Mapped[int] = mapped_column(...)
    winery_id: Mapped[int] = mapped_column(...)
    vintage_year: Mapped[int] = mapped_column(...)
    # ... more fields
    
    # Relationships
    notes: Mapped[List["FermentationNote"]] = relationship(...)
    lot_sources: Mapped[List["FermentationLotSource"]] = relationship(...)
```

**Your Protocol entities will follow EXACT same pattern**:

```python
class FermentationProtocol(BaseEntity):
    __tablename__ = "fermentation_protocols"
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"))
    varietal_code: Mapped[str] = mapped_column(String(10))
    # ... more fields
    
    # Relationships
    steps: Mapped[List["ProtocolStep"]] = relationship(...)
    executions: Mapped[List["ProtocolExecution"]] = relationship(...)
```

**No new patterns needed - just apply existing SQLAlchemy code style** ✅

---

## ✅ Summary: Ready to Code?

### YES FOR:
- ✅ Domain entities (exact schema in ADR-035)
- ✅ Enums (exact values in ADR-035)
- ✅ Repository interfaces (pattern from existing code)
- ✅ Database migration (SQL in ADR-035)

### WAITING ON:
- ⏳ Protocol data (PDF extractions - your responsibility)
- ⏳ Seed script (depends on extractions)
- ⏳ Full service testing (need real data in database)

### RECOMMENDATION:

**Start TODAY with domain entities + enums** (1 hour, no blockers)

**Do repositories TOMORROW** (3 hours, completes data access layer)

**Extract protocols THIS WEEK** (2-3 days, your manual work)

**Load database NEXT WEEK** (1 hour, production data)

**By Feb 20**: Full Protocol Engine ready for feature development

---

## 📚 Reference Files

- [ADR-035](./ai-context/adr/ADR-035-protocol-data-model-schema.md) - Complete schema, enums, SQL
- [PROTOCOL-EXTRACTION-GUIDE](./PROTOCOL-EXTRACTION-GUIDE.md) - How to extract PDFs
- [PROTOCOL-NEXT-ACTIONS](./PROTOCOL-NEXT-ACTIONS.md) - Timeline and priorities

