# ADR-035: Protocol Compliance Engine - Data Model & Schema Design

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team  
**Related ADRs**: ADR-021 (Protocol Engine), ADR-025 (Multi-tenancy)  
**Timeline Context**: May 2026 demo deadline (10 weeks)

---

## Context and Problem Statement

The Protocol Compliance Engine requires a robust data model that:
1. **Captures protocol definitions** (master templates for varietals)
2. **Tracks execution** (per-fermentation protocol tracking)
3. **Audits compliance** (step completions with timestamps and justifications)
4. **Supports versioning** (protocol changes over time)
5. **Enables multi-winery use** (Napa Valley context, isolated per winery)

From **AI Enologist analysis**, we know:
- Red wines: 15-30 steps, 18-30 day fermentation
- White wines: 20-40 steps, 14-28 day fermentation
- Step types: ~10-15 common types (YEAST_INOCULATION, H2S_CHECK, DAP_ADDITION, etc.)
- Criticality varies by varietal (Pinot Noir ≠ Cabernet for H2S sensitivity)
- Tolerance windows: ±4-8 hours for critical, ±3-5 days for optional

---

## Decision

### Entity Model

#### 1. **FermentationProtocol** (Master Template)
```python
class FermentationProtocol(BaseEntity):
    """Master protocol definition for a varietal/winery"""
    
    id: int
    winery_id: int  # Multi-tenancy
    varietal_code: str  # "CS", "CH", "PN"
    varietal_name: str  # "Cabernet Sauvignon"
    version: str  # "1.0", "2.0", "2.1"
    protocol_name: str  # "CS-2026-Standard"
    description: str  # Long text
    color: str  # "RED" or "WHITE"
    expected_duration_days: int  # Typical fermentation length
    
    # Metadata
    is_active: bool  # Currently in use?
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    steps: List[ProtocolStep]  # Ordered list
    executions: List[ProtocolExecution]  # Historical executions
    
    # Constraints
    unique_constraint: (winery_id, varietal_code, version)
    check_constraint: version_format MATCHES "^\d+\.\d+$"
```

**Why this design:**
- ✅ `varietal_code` + `version` allows protocol evolution (v1.0 → v2.0 → v2.1)
- ✅ `is_active` allows multiple versions but only one active per varietal
- ✅ `expected_duration_days` helps validate early completion
- ✅ `color` enables RED/WHITE specific logic (different monitoring patterns)

---

#### 2. **ProtocolStep** (Ordered Step Definition)
```python
class ProtocolStep(BaseEntity):
    """Single step within a protocol"""
    
    id: int
    protocol_id: int  # Foreign key
    step_order: int  # 1, 2, 3, ... (must be unique per protocol)
    step_type: StepType  # Enum
    description: str  # "Add DAP at 1/3 sugar depletion"
    
    # Timing
    expected_day: int  # Which day? (0=crush day, 1=next day, etc.)
    tolerance_hours: int  # ±N hours window
    duration_minutes: int  # How long does this task take?
    
    # Criticality
    is_critical: bool  # Critical to wine quality?
    criticality_score: float  # 0-100 (for weighted compliance)
    
    # Dependencies
    depends_on_step_id: Optional[int]  # Must complete step X first?
    can_repeat_daily: bool  # Can this step be done 2x/day? (e.g., TEMP_CHECK)
    
    # Metadata
    notes: str  # Additional instructions
    
    # Relationships
    protocol: FermentationProtocol
    completions: List[StepCompletion]
    
    # Constraints
    unique_constraint: (protocol_id, step_order)
    check_constraint: expected_day >= 0
    check_constraint: tolerance_hours >= 0
```

**Why this design:**
- ✅ `step_order` enforces sequence (immutable)
- ✅ `tolerance_hours` captures Napa-specific timing requirements
- ✅ `can_repeat_daily` handles steps like temperature checks (multiple/day)
- ✅ `depends_on_step_id` models hard dependencies
- ✅ Flexible enough for reds vs whites differences

**Step Type Examples (Enum)**:
```python
class StepType(str, Enum):
    YEAST_INOCULATION = "YEAST_INOCULATION"
    H2S_CHECK = "H2S_CHECK"
    TEMPERATURE_CHECK = "TEMPERATURE_CHECK"
    BRIX_READING = "BRIX_READING"
    DAP_ADDITION = "DAP_ADDITION"
    NUTRIENT_ADDITION = "NUTRIENT_ADDITION"
    PUNCH_DOWN = "PUNCH_DOWN"
    PUMP_OVER = "PUMP_OVER"
    SO2_ADDITION = "SO2_ADDITION"
    PRESSING = "PRESSING"
    COLD_SOAK = "COLD_SOAK"
    MLF_INOCULATION = "MLF_INOCULATION"
    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    CATA_TASTING = "CATA_TASTING"
    RACKING = "RACKING"
    FILTERING = "FILTERING"
    CLARIFICATION = "CLARIFICATION"
```

---

#### 3. **ProtocolExecution** (Per-Fermentation Tracking)
```python
class ProtocolExecution(BaseEntity):
    """Tracks protocol adherence for a specific fermentation"""
    
    id: int
    fermentation_id: int  # Links to Fermentation
    protocol_id: int  # Which protocol being followed?
    winery_id: int  # Multi-tenancy
    
    # Execution state
    start_date: datetime  # When fermentation started (= protocol day 0)
    status: ProtocolExecutionStatus  # NOT_STARTED, ACTIVE, COMPLETED, PAUSED
    
    # Compliance tracking
    compliance_score: float  # 0-100%
    completed_steps: int  # Count of completed steps
    skipped_critical_steps: int  # Count of critical steps not done
    
    # Notes
    notes: str  # General execution notes
    
    # Metadata
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Relationships
    protocol: FermentationProtocol
    fermentation: Fermentation
    completions: List[StepCompletion]  # All step logs
    
    # Constraints
    unique_constraint: (fermentation_id)  # One execution per fermentation
    check_constraint: compliance_score BETWEEN 0 AND 100
```

**Status Values**:
```python
class ProtocolExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"     # Protocol assigned, not started
    ACTIVE = "ACTIVE"               # Fermentation in progress
    PAUSED = "PAUSED"               # Fermentation paused (stuck, etc.)
    COMPLETED = "COMPLETED"         # Fermentation done, protocol finished
    ABANDONED = "ABANDONED"         # Fermentation failed/discarded
```

---

#### 4. **StepCompletion** (Audit Log Entry)
```python
class StepCompletion(BaseEntity):
    """Record of when/how a step was completed (audit trail)"""
    
    id: int
    execution_id: int  # Foreign key
    step_id: int  # Which step?
    
    # Completion details
    completed_at: datetime  # When was it actually done?
    notes: str  # What did you observe? (optional observations)
    
    # Status
    is_on_schedule: bool  # Completed within tolerance window?
    days_late: int  # 0 if on time, >0 if late
    
    # Skip/Deviation handling
    was_skipped: bool  # True if marked as skipped (not completed)
    skip_reason: Optional[SkipReason]  # Why was it skipped?
    skip_notes: Optional[str]  # Detailed justification
    
    # Verification
    verified_by_user_id: Optional[int]  # Who logged this?
    
    # Metadata
    created_at: datetime  # When logged in system
    
    # Relationships
    execution: ProtocolExecution
    step: ProtocolStep
    user: User
    
    # Constraints
    unique_constraint: (execution_id, step_id, completed_at)
    check_constraint: (was_skipped=true XOR completed_at IS NOT NULL)
```

**Skip Reason Enum**:
```python
class SkipReason(str, Enum):
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    CONDITION_NOT_MET = "CONDITION_NOT_MET"  # "pH already correct"
    FERMENTATION_ENDED = "FERMENTATION_ENDED"  # "Brix < 0, ferment done"
    FERMENTATION_FAILED = "FERMENTATION_FAILED"  # "Tank lost to contamination"
    WINEMAKER_DECISION = "WINEMAKER_DECISION"  # "Tasting indicated not needed"
    REPLACED_BY_ALTERNATIVE = "REPLACED_BY_ALTERNATIVE"  # "Used micro-ox instead of pump"
    OTHER = "OTHER"  # Free-text justification required
```

---

### Database Schema

```sql
CREATE TABLE fermentation_protocols (
    id SERIAL PRIMARY KEY,
    winery_id INTEGER NOT NULL,
    varietal_code VARCHAR(10) NOT NULL,
    varietal_name VARCHAR(100) NOT NULL,
    version VARCHAR(10) NOT NULL,
    protocol_name VARCHAR(200) NOT NULL,
    description TEXT,
    color VARCHAR(10) CHECK (color IN ('RED', 'WHITE')),
    expected_duration_days INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (winery_id) REFERENCES wineries(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    UNIQUE (winery_id, varietal_code, version),
    CHECK (expected_duration_days > 0)
);

CREATE TABLE protocol_steps (
    id SERIAL PRIMARY KEY,
    protocol_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    expected_day INTEGER NOT NULL,
    tolerance_hours INTEGER NOT NULL DEFAULT 0,
    duration_minutes INTEGER NOT NULL DEFAULT 0,
    is_critical BOOLEAN DEFAULT false,
    criticality_score FLOAT DEFAULT 1.0,
    depends_on_step_id INTEGER,
    can_repeat_daily BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (protocol_id) REFERENCES fermentation_protocols(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_step_id) REFERENCES protocol_steps(id),
    UNIQUE (protocol_id, step_order),
    CHECK (expected_day >= 0),
    CHECK (tolerance_hours >= 0),
    CHECK (criticality_score BETWEEN 0 AND 100)
);

CREATE TABLE protocol_executions (
    id SERIAL PRIMARY KEY,
    fermentation_id INTEGER NOT NULL,
    protocol_id INTEGER NOT NULL,
    winery_id INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    compliance_score FLOAT DEFAULT 0.0,
    completed_steps INTEGER DEFAULT 0,
    skipped_critical_steps INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (fermentation_id) REFERENCES fermentations(id),
    FOREIGN KEY (protocol_id) REFERENCES fermentation_protocols(id),
    FOREIGN KEY (winery_id) REFERENCES wineries(id),
    UNIQUE (fermentation_id),
    CHECK (compliance_score BETWEEN 0 AND 100)
);

CREATE TABLE step_completions (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    completed_at TIMESTAMP,
    notes TEXT,
    is_on_schedule BOOLEAN,
    days_late INTEGER DEFAULT 0,
    was_skipped BOOLEAN DEFAULT false,
    skip_reason VARCHAR(50),
    skip_notes TEXT,
    verified_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES protocol_executions(id),
    FOREIGN KEY (step_id) REFERENCES protocol_steps(id),
    FOREIGN KEY (verified_by_user_id) REFERENCES users(id),
    UNIQUE (execution_id, step_id),
    CHECK ((was_skipped = true AND skip_reason IS NOT NULL) OR was_skipped = false)
);

CREATE INDEX idx_protocols_winery_active ON fermentation_protocols(winery_id, is_active);
CREATE INDEX idx_protocols_varietal ON fermentation_protocols(winery_id, varietal_code);
CREATE INDEX idx_executions_fermentation ON protocol_executions(fermentation_id);
CREATE INDEX idx_executions_status ON protocol_executions(winery_id, status);
CREATE INDEX idx_completions_execution ON step_completions(execution_id);
CREATE INDEX idx_completions_completed_at ON step_completions(completed_at);
```

---

## Consequences

### Positive ✅
- **Flexible versioning**: Protocols evolve over time
- **Comprehensive audit trail**: Every step logged with justification
- **Multi-tenancy safe**: Winery isolation enforced at schema level
- **Supports both red/white**: Color-specific logic possible
- **Performance**: Indexes on common queries (<100ms)
- **Data integrity**: Constraints prevent invalid states

### Negative ⚠️
- **Complexity**: 4 tables with cross-references (mitigated by clear relationships)
- **Storage**: Every step logged means more rows (mitigated by archival strategy)
- **Cascading deletes**: Protocol deletion affects steps (handled by ON DELETE CASCADE)

---

## Migration Path

1. **Week 1**: Create tables + indexes
2. **Week 1**: Load sample protocols from Susana's PDFs (seed data)
3. **Week 2**: Implement repositories (CRUD operations)
4. **Week 2**: Integration tests with sample data
5. **Week 3+**: Service layer implementation

---

## Questions for Susana (If Not Yet Answered)

- [ ] Should we retain deleted protocols for historical analysis? (soft delete?)
- [ ] Protocol comparison: should we track which version was used per fermentation?
- [ ] Can a protocol be applied retroactively to past fermentations for analysis?

