# ADR-021: Fermentation Protocol Compliance Engine

**Status**: 📋 Proposed (Pending Real Protocol Validation)  
**Date**: February 6, 2026  
**Decision Makers**: Development Team + Enologist (Susana Rodriguez Vasquez)  
**Related ADRs**: ADR-020 (Analysis Engine), ADR-019 (ETL Pipeline), ADR-027 (Logging)

---

## Context and Problem Statement

Bodegas como LangeTwins tienen protocolos de fermentación específicos por varietal (Cabernet, Chardonnay, etc.). Estos protocolos definen:
- Pasos ordenados (inoculación, adiciones de nutrientes, etc.)
- Condiciones trigger ("cuando Brix < 18", "día 5 de fermentación")
- Mediciones esperadas ("5×10⁶ células/mL", "contar levaduras")
- Tolerancias ("±2 días", "±0.2 Brix puntos")

**Business Goals**:
- ✅ **Guía a enólogos**: Checklist en tiempo real, recordatorios de próximos pasos
- ✅ **Auditoría de cumplimiento**: Registrar qué se hizo, cuándo, por quién
- ✅ **Detectar desviaciones**: Pasos saltados, fuera de tolerancia
- ✅ **Mejora continua**: Correlacionar cumplimiento con calidad final
- ✅ **Entrenamiento**: Estandarizar prácticas exitosas

**Technical Requirements**:
- **Persistence**: Protocolos guardados, ejecuciones auditadas
- **Real-time Alerts**: "Próximo paso: H₂S check" en app
- **Integration**: Embebido en Analysis Engine (ADR-020)
- **Performance**: Lookup protocolo <100ms
- **Multi-tenancy**: Cada bodega su protocolo

**Current State**:
- ✅ Protocols existen (en papel/Excel de Susana)
- ❌ No digitalizados
- ❌ Sin tracking de cumplimiento
- ❌ Sin correlación con Analysis Engine

---

## Business Context (From Enologist Interview)

**Susana's Workflow** (Actual):

```
Día 0: Inocular lote CS-001
  → Contar levaduras (microscopic)
  → Registrar Brix inicial
  
Día 1: ✓ Done
  → Agregar DAP 1-2 lbs/1000 gal
  → Registrar temperatura
  
Día 3: ⚠️ MISSED
  → Contar levaduras YAN
  → Verificar fermentación en marcha
  
Día 5: ✓ Done
  → Primer remontaje (3 horas)
  → Aumentar tiempo si pieles gruesas
  
Día 8: 🚫 NOT LOGGED
  → Visual check H₂S (olor)
  → Cata del jugo
  
...

Resultado: 92% compliance (missed H₂S check caused VA spike)
```

**Key Insight**: Enologist sabe qué hacer, pero sin sistema:
- Olvida pasos (especialmente los "invisible" como H₂S check)
- No hay registro para auditoría
- No puede correlacionar "skipped H₂S → VA problema"

---

## Decision

### Architecture

**New Entities**:

```python
# database/entities/fermentation_protocol.py

class FermentationProtocol(Base):
    """Master protocol for varietal/winery"""
    __tablename__ = "fermentation_protocols"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"))
    varietal_code: Mapped[str] = Column(String(10))  # "CS", "CH", "PN"
    varietal_name: Mapped[str] = Column(String(100))  # "Cabernet Sauvignon"
    version: Mapped[int] = Column(Integer, default=1)  # v1, v2, v3
    name: Mapped[str] = Column(String(200))  # "CS-2026-Standard"
    description: Mapped[str] = Column(String(1000), nullable=True)
    
    # Lifecycle
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Relationships
    winery: Mapped["Winery"] = relationship("Winery")
    steps: Mapped[List["ProtocolStep"]] = relationship(
        "ProtocolStep",
        back_populates="protocol",
        cascade="all, delete-orphan",
        foreign_keys="ProtocolStep.protocol_id"
    )
    executions: Mapped[List["ProtocolExecution"]] = relationship(
        "ProtocolExecution",
        back_populates="protocol"
    )
    
    __table_args__ = (
        UniqueConstraint("winery_id", "varietal_code", "version", 
                        name="uq_protocol_per_varietal_version"),
    )


class ProtocolStep(Base):
    """Individual step in protocol"""
    __tablename__ = "protocol_steps"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("fermentation_protocols.id"))
    sequence: Mapped[int] = Column(Integer)  # 1, 2, 3...
    title: Mapped[str] = Column(String(200))  # "Inoculation"
    description: Mapped[str] = Column(String(1000))
    
    # Trigger condition
    trigger_type: Mapped[str] = Column(String(50))  # "DAY", "BRIX", "TIME_ELAPSED"
    trigger_value: Mapped[str] = Column(String(100))  # "0", "<18", "48_HOURS"
    trigger_description: Mapped[str] = Column(String(200))  # "On day 0"
    
    # Expected action
    action_description: Mapped[str] = Column(String(500))
    expected_duration_hours: Mapped[Optional[int]] = Column(Integer, nullable=True)
    
    # Measurement
    measurement_required: Mapped[str] = Column(String(300))  # "Count yeast cells/mL"
    measurement_unit: Mapped[Optional[str]] = Column(String(50), nullable=True)  # "cells/mL"
    expected_value: Mapped[Optional[str]] = Column(String(100), nullable=True)  # "5×10^6"
    tolerance_low: Mapped[Optional[float]] = Column(Float, nullable=True)  # 4.8
    tolerance_high: Mapped[Optional[float]] = Column(Float, nullable=True)  # 5.2
    
    # Criticality
    is_critical: Mapped[bool] = Column(Boolean, default=False)  # Can't skip
    
    # Notes
    notes: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # Relationships
    protocol: Mapped["FermentationProtocol"] = relationship(
        "FermentationProtocol",
        back_populates="steps"
    )
    executions: Mapped[List["ExecutedProtocolStep"]] = relationship(
        "ExecutedProtocolStep",
        back_populates="protocol_step"
    )
    
    __table_args__ = (
        UniqueConstraint("protocol_id", "sequence", name="uq_step_sequence_per_protocol"),
    )


class ProtocolExecution(Base):
    """Audit trail: how a fermentation followed (or didn't) the protocol"""
    __tablename__ = "protocol_executions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    fermentation_id: Mapped[int] = mapped_column(ForeignKey("fermentations.id"))
    protocol_id: Mapped[int] = mapped_column(ForeignKey("fermentation_protocols.id"))
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"))
    
    # Status
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # Audit
    total_steps: Mapped[int] = Column(Integer)
    completed_steps: Mapped[int] = Column(Integer, default=0)
    on_time_steps: Mapped[int] = Column(Integer, default=0)
    late_steps: Mapped[int] = Column(Integer, default=0)
    skipped_steps: Mapped[int] = Column(Integer, default=0)
    within_tolerance_steps: Mapped[int] = Column(Integer, default=0)
    out_of_tolerance_steps: Mapped[int] = Column(Integer, default=0)
    critical_steps_skipped: Mapped[int] = Column(Integer, default=0)
    
    # Overall compliance
    compliance_percentage: Mapped[float] = Column(Float, default=0.0)  # 0-100
    
    # Notes
    notes: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    
    # Relationships
    fermentation: Mapped["Fermentation"] = relationship("Fermentation")
    protocol: Mapped["FermentationProtocol"] = relationship("FermentationProtocol")
    winery: Mapped["Winery"] = relationship("Winery")
    executed_steps: Mapped[List["ExecutedProtocolStep"]] = relationship(
        "ExecutedProtocolStep",
        back_populates="protocol_execution",
        cascade="all, delete-orphan"
    )


class ExecutedProtocolStep(Base):
    """What actually happened vs what was planned"""
    __tablename__ = "executed_protocol_steps"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    protocol_execution_id: Mapped[int] = mapped_column(ForeignKey("protocol_executions.id"))
    protocol_step_id: Mapped[int] = mapped_column(ForeignKey("protocol_steps.id"))
    
    # Timeline
    expected_trigger_date: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    actual_execution_date: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # Status
    status: Mapped[str] = Column(String(20))  # "COMPLETED", "SKIPPED", "PENDING"
    
    # Measurement
    actual_value: Mapped[Optional[str]] = Column(String(100), nullable=True)
    is_within_tolerance: Mapped[Optional[bool]] = Column(Boolean, nullable=True)
    tolerance_error: Mapped[Optional[str]] = Column(String(200), nullable=True)
    
    # Who did it
    executed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = Column(String(500), nullable=True)
    
    # Relationships
    protocol_execution: Mapped["ProtocolExecution"] = relationship(
        "ProtocolExecution",
        back_populates="executed_steps"
    )
    protocol_step: Mapped["ProtocolStep"] = relationship(
        "ProtocolStep",
        back_populates="executions"
    )
    executed_by: Mapped[Optional["User"]] = relationship("User")
```

---

## Service Layer

### ProtocolService

```python
class ProtocolService:
    """CRUD for protocols"""
    
    async def create_protocol(
        self,
        winery_id: int,
        varietal_code: str,
        varietal_name: str,
        name: str,
        created_by_user_id: int,
        description: Optional[str] = None
    ) -> FermentationProtocol:
        """Create new protocol version"""
        
    async def add_step(
        self,
        protocol_id: int,
        sequence: int,
        title: str,
        trigger_type: str,  # "DAY", "BRIX"
        trigger_value: str,  # "0", "<18"
        action_description: str,
        measurement_required: str,
        expected_value: Optional[str] = None,
        tolerance_low: Optional[float] = None,
        tolerance_high: Optional[float] = None,
        is_critical: bool = False
    ) -> ProtocolStep:
        """Add step to protocol"""
        
    async def get_protocol_for_varietal(
        self,
        winery_id: int,
        varietal_code: str,
        version: Optional[int] = None  # Latest if None
    ) -> Optional[FermentationProtocol]:
        """Get active protocol for varietal"""
        
    async def list_protocols(
        self,
        winery_id: int,
        varietal_code: Optional[str] = None
    ) -> List[FermentationProtocol]:
        """List all protocols for winery"""
```

### ProtocolComplianceService

```python
class ProtocolComplianceService:
    """Track & analyze protocol compliance"""
    
    async def start_protocol_tracking(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> ProtocolExecution:
        """Initialize protocol execution for new fermentation"""
        # 1. Get varietal from fermentation
        # 2. Find active protocol
        # 3. Create ProtocolExecution
        # 4. Return for tracking
        
    async def record_step_execution(
        self,
        fermentation_id: int,
        protocol_step_id: int,
        actual_value: Optional[str] = None,
        executed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> ExecutedProtocolStep:
        """Record that a step was executed"""
        # 1. Find active ProtocolExecution
        # 2. Create ExecutedProtocolStep
        # 3. Check if within tolerance
        # 4. Update compliance stats
        # 5. Check if critical step skipped → trigger anomaly
        
    async def detect_missed_steps(
        self,
        fermentation_id: int,
        current_date: datetime
    ) -> List[ProtocolStep]:
        """Return steps that SHOULD have been done but weren't"""
        # 1. Get active ProtocolExecution
        # 2. For each step: check if trigger condition met
        # 3. If triggered but not executed: return as missed
        # 4. Integrate with Analysis Engine: yield WARNING anomaly
        
    async def calculate_compliance(
        self,
        protocol_execution_id: int
    ) -> float:
        """0-100% compliance score"""
        # Weighting:
        # - Critical steps not skipped: +50%
        # - Steps within tolerance: +40%
        # - Steps on-time: +10%
        
    async def get_protocol_execution_status(
        self,
        fermentation_id: int
    ) -> ProtocolExecutionStatusDTO:
        """Current status of protocol compliance"""
        # Returns:
        # - Current step
        # - Next steps
        # - Missed steps
        # - Compliance %
        # - Anomalies
```

---

## API Endpoints

### Create/Manage Protocols

```http
# Create new protocol
POST /api/protocols
{
  "varietal_code": "CS",
  "varietal_name": "Cabernet Sauvignon",
  "name": "CS-2026-Standard-v1",
  "description": "Standard protocol for CS fermentation at LangeTwins"
}
→ 201 Created

# Add step to protocol
POST /api/protocols/{protocol_id}/steps
{
  "sequence": 1,
  "title": "Inoculation",
  "trigger_type": "DAY",
  "trigger_value": "0",
  "action_description": "Prepare pie de cuba. Count yeast cells.",
  "measurement_required": "Yeast cell count",
  "measurement_unit": "cells/mL",
  "expected_value": "5e6",
  "tolerance_low": 4.8,
  "tolerance_high": 5.2,
  "is_critical": true
}
→ 201 Created

# Get protocol details
GET /api/protocols/{protocol_id}
→ Full protocol with all steps

# List protocols
GET /api/protocols?winery_id=1&varietal_code=CS
→ All versions of CS protocol
```

### Track Compliance

```http
# Start tracking for fermentation
POST /api/fermentations/{fermentation_id}/protocol-tracking
{
  "protocol_id": 5
}
→ 201 Created ProtocolExecution

# Record step execution
POST /api/fermentations/{fermentation_id}/protocol-steps/{step_id}/execute
{
  "actual_value": "5.1e6",
  "executed_by_user_id": 42,
  "notes": "Counted 3 samples, average"
}
→ 200 OK, ExecutedProtocolStep

# Check what's missing
GET /api/fermentations/{fermentation_id}/protocol-status
→ {
    "compliance_percentage": 92,
    "current_step": 5,
    "next_steps": [
      {
        "sequence": 5,
        "title": "First Remontage",
        "trigger": "Day 5",
        "action": "3 hours, increase for thick-skin varieties"
      }
    ],
    "missed_steps": [
      {
        "sequence": 3,
        "title": "YAN Count",
        "was_due": "2026-02-04",
        "is_critical": false,
        "recommendation": "Still can perform"
      }
    ],
    "anomalies": [
      {
        "type": "PROTOCOL_STEP_CRITICAL_SKIPPED",
        "step": "H₂S Visual Check (Day 8)",
        "severity": "WARNING"
      }
    ]
  }

# Get compliance history
GET /api/fermentations/{fermentation_id}/protocol-execution
→ Full audit trail
```

---

## Integration with Analysis Engine (ADR-020)

**New Anomaly Types**:

```python
class AnomalyType(str, Enum):
    # ... existing from ADR-020 ...
    
    # NEW - Protocol deviations
    PROTOCOL_STEP_SKIPPED = "PROTOCOL_STEP_SKIPPED"
    PROTOCOL_STEP_CRITICAL_SKIPPED = "PROTOCOL_STEP_CRITICAL_SKIPPED"
    PROTOCOL_STEP_OUT_OF_TOLERANCE = "PROTOCOL_STEP_OUT_OF_TOLERANCE"
    PROTOCOL_LOW_COMPLIANCE = "PROTOCOL_LOW_COMPLIANCE"
```

**Service Integration**:

```python
# In AnalysisOrchestratorService

async def analyze_fermentation(fermentation_id: int, winery_id: int):
    # ... existing analysis logic ...
    
    # NEW: Check protocol compliance
    protocol_compliance = await self.protocol_compliance_service.get_protocol_execution_status(
        fermentation_id
    )
    
    # If critical steps skipped → ANOMALY
    if protocol_compliance.critical_steps_skipped > 0:
        for skipped in protocol_compliance.skipped_critical_steps:
            yield Anomaly(
                type=AnomalyType.PROTOCOL_STEP_CRITICAL_SKIPPED,
                description=f"Critical step skipped: {skipped.title}",
                severity=SeverityLevel.WARNING
            )
    
    # If compliance < threshold → WARNING
    if protocol_compliance.compliance_percentage < 85:
        yield Anomaly(
            type=AnomalyType.PROTOCOL_LOW_COMPLIANCE,
            description=f"Protocol compliance only {protocol_compliance.compliance_percentage}%",
            severity=SeverityLevel.WARNING
        )
```

---

## Data Model (Tentative - Pending Real Protocol)

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| varietal_code | STRING | "CS" | Cabernet Sauvignon |
| protocol_name | STRING | "CS-2026-Standard-v1" | Human readable |
| step.trigger_type | ENUM | DAY, BRIX, TIME_ELAPSED | How to know when to do it |
| step.trigger_value | STRING | "0", "<18", "48_HOURS" | Condition value |
| step.is_critical | BOOLEAN | true/false | Can't skip |
| step.measurement_required | STRING | "Yeast count", "H₂S visual" | What to measure |
| tolerance_range | RANGE | [4.8, 5.2] | Acceptable deviation |

---

## Test Strategy

### Unit Tests

```python
# tests/unit/analysis_engine/services/test_protocol_service.py

async def test_create_protocol():
    protocol = await service.create_protocol(...)
    assert protocol.varietal_code == "CS"
    assert protocol.version == 1
    
async def test_add_step_to_protocol():
    step = await service.add_step(...)
    assert step.sequence == 1
    assert step.is_critical == True
    
async def test_calculate_compliance_perfect():
    # All steps on-time, within tolerance
    compliance = await service.calculate_compliance(execution_id)
    assert compliance == 100.0
    
async def test_calculate_compliance_with_deviations():
    # Some late, some out of tolerance
    compliance = await service.calculate_compliance(execution_id)
    assert 85 <= compliance < 100
    
async def test_detect_missed_critical_steps():
    # Trigger PROTOCOL_STEP_CRITICAL_SKIPPED anomaly
    missed = await service.detect_missed_steps(fermentation_id, datetime.now())
    assert len(missed) > 0
    assert any(s.is_critical for s in missed)
```

### Integration Tests

```python
# tests/integration/analysis_engine/test_protocol_compliance_flow.py

async def test_full_protocol_execution_flow():
    # 1. Create protocol with 5 steps
    # 2. Start fermentation with protocol tracking
    # 3. Execute steps 1, 2, 4 (skip 3, missing 5)
    # 4. Calculate compliance
    # 5. Verify anomalies generated
    # 6. Verify Analysis Engine picks them up
```

---

## Implementation Phases

### Phase 1: Domain + Repository (Week 1)
- [ ] Domain entities (Protocol, Step, Execution, ExecutedStep)
- [ ] Repositories (CRUD)
- [ ] Unit tests (40 tests expected)
- [ ] **Pending**: Real protocol example from Susana

### Phase 2: Service Layer (Week 2)
- [ ] ProtocolService (CRUD operations)
- [ ] ProtocolComplianceService (tracking, compliance calculation)
- [ ] Integration tests
- [ ] **Pending**: Enologist validation

### Phase 3: API Layer (Week 2)
- [ ] FastAPI endpoints
- [ ] DTOs with Pydantic
- [ ] API tests (20+ tests)
- [ ] **Pending**: UX review with Susana

### Phase 4: Analysis Engine Integration (Week 3)
- [ ] New Anomaly types
- [ ] AnalysisOrchestratorService integration
- [ ] End-to-end tests
- [ ] **Pending**: UAT with enologist

### Phase 5: Dashboard/UI (Week 3-4)
- [ ] Real-time protocol checklist
- [ ] Compliance visualization
- [ ] Alerts for missed steps
- [ ] **Pending**: Designer review

---

## Open Questions (Waiting for Real Protocol)

1. **Trigger conditions**: Are there more than DAY, BRIX, TIME_ELAPSED?
   - Example: "After VA test result < 0.3"?

2. **Measurement granularity**: How exact?
   - "Exactly 5e6" vs "5e6 ±10%" vs qualitative ("visible fermentation")?

3. **Step dependencies**: Can step 5 start before step 4 completes?
   - Or strict sequential?

4. **Variability**: Does CS protocol differ by:
   - Fruit origin (Lodi vs Paso Robles)?
   - Harvest year?
   - Acid level?

5. **Versioning**: How often does protocol change?
   - Per vintage? Per experimental batch?

---

## Success Criteria

- ✅ 100% of protocol steps can be represented
- ✅ Real-time tracking without manual workarounds
- ✅ < 2 second endpoint latency
- ✅ 90%+ accuracy in anomaly detection vs manual review
- ✅ Enologist confirms "This is how I actually work"
- ✅ 50+ tests all passing

---

## References

- ADR-020: Analysis Engine Architecture
- ADR-027: Structured Logging & Observability
- ADR-034: Historical Data Service Refactoring
- Enologist Interview: Susana Rodriguez Vasquez (Feb 1, 2026)

---

## Status Tracking

| Item | Status | Owner | Due |
|------|--------|-------|-----|
| Get real protocol from Susana | ⏳ Pending | User | Feb 10 |
| Validate data model | ⏳ Pending | User + Dev | Feb 12 |
| Phase 1 implementation | 🚀 Ready | Dev | Feb 19 |
| Enologist UAT | ⏳ Pending | Susana | Feb 26 |

