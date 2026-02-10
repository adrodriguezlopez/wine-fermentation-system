# ADR-039: Protocol Template Management & Customization

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team  
**Related ADRs**: ADR-035 (Data Model), ADR-021 (Protocol Engine)  
**Timeline Context**: Phase 1-2 implementation (Week 3-4)

---

## Context and Problem Statement

Winery needs flexibility in managing fermentation protocols:

1. **Template Library**: Standard protocols for common varietals (CS, PN, CH, etc.)
2. **Customization**: Modify templates for specific lots (LangeTwins 2026 Pinot ≠ Silverado 2026 Pinot)
3. **Versioning**: Track protocol evolution (v1.0 → v2.0 after learnings)
4. **Reuse**: Template → multiple fermentations without re-entering steps
5. **Governance**: Control who can create/modify protocols (admin vs winemaker)

---

## Decision

### Protocol Lifecycle States

```
┌──────────────┐
│   TEMPLATE   │  Master definition (admin-only)
│ (Draft/Final)│  ex: "Cabernet Sauvignon Standard v2.0"
└────┬─────────┘
     │ Copy for customization
     ▼
┌──────────────────┐
│   ASSIGNMENT     │  Assigned to specific fermentation
│ (Pending/Active) │  Can override steps before fermentation starts
└────┬─────────────┘
     │ Fermentation begins
     ▼
┌──────────────────┐
│   EXECUTION      │  Immutable once started
│  (Active/Done)   │  Track all completions
└──────────────────┘
```

### Template State Management

```python
class FermentationProtocol(BaseEntity):
    # ... existing fields ...
    
    # Lifecycle state
    state: ProtocolState  # DRAFT, FINAL, DEPRECATED
    is_template: bool  # True = master, False = instance-specific
    
    # Template tracking
    template_id: Optional[int]  # If instance, links to parent template
    template_version: Optional[str]  # Which version was copied from?
    
    # Modification tracking
    changes_from_template: List[ProtocolChange]  # What was modified?
    
    # Governance
    created_by_user_id: int
    approved_by_user_id: Optional[int]
    
    # Scheduling
    effective_start_date: date  # When does this template take effect?
    effective_end_date: Optional[date]  # Retire old template after date
    
    class ProtocolState(str, Enum):
        DRAFT = "DRAFT"           # Still being edited
        FINAL = "FINAL"           # Approved, in use
        DEPRECATED = "DEPRECATED" # Old, replaced by newer version
```

---

### Template Management Operations

#### 1. Create New Template

```python
def create_protocol_template(
    winery_id: int,
    varietal_code: str,
    varietal_name: str,
    color: str,
    version: str,
    expected_duration_days: int,
    steps: List[StepDefinition],
    created_by_user: User
) -> FermentationProtocol:
    """
    Admin-only: Create new master protocol template.
    """
    
    # Authorization check
    if created_by_user.role not in [UserRole.ADMIN]:
        raise PermissionError("Only admins can create templates")
    
    # Validate version format
    if not re.match(r"^\d+\.\d+$", version):
        raise ValueError("Version must be X.Y format (e.g., 1.0, 2.1)")
    
    # Check for duplicates
    existing = FermentationProtocol.filter(
        winery_id=winery_id,
        varietal_code=varietal_code,
        version=version
    )
    if existing:
        raise ValueError(f"Protocol {varietal_code} v{version} already exists")
    
    protocol = FermentationProtocol.create(
        winery_id=winery_id,
        varietal_code=varietal_code,
        varietal_name=varietal_name,
        color=color,
        version=version,
        protocol_name=f"{varietal_name} {version}",
        expected_duration_days=expected_duration_days,
        is_template=True,
        state=ProtocolState.DRAFT,
        created_by_user_id=created_by_user.id
    )
    
    # Add steps
    for idx, step_def in enumerate(steps):
        ProtocolStep.create(
            protocol_id=protocol.id,
            step_order=idx + 1,
            step_type=step_def.type,
            description=step_def.description,
            expected_day=step_def.expected_day,
            tolerance_hours=step_def.tolerance_hours,
            is_critical=step_def.is_critical,
            criticality_score=step_def.criticality_score,
            # ... other fields
        )
    
    logger.info(f"Created template: {protocol.protocol_name}")
    return protocol
```

#### 2. Approve Template (Draft → Final)

```python
def approve_protocol_template(
    protocol_id: int,
    approved_by_user: User,
    effective_date: Optional[date] = None
) -> FermentationProtocol:
    """
    Admin-only: Move template from DRAFT to FINAL (ready to use).
    """
    
    protocol = FermentationProtocol.get(id=protocol_id)
    
    # Authorization
    if approved_by_user.role not in [UserRole.ADMIN]:
        raise PermissionError("Only admins can approve templates")
    
    # Must be DRAFT
    if protocol.state != ProtocolState.DRAFT:
        raise ValueError(f"Can only approve DRAFT templates, current state: {protocol.state}")
    
    # Validation: all steps defined?
    if not protocol.steps:
        raise ValueError("Cannot approve template with no steps")
    
    # Must have sequential step orders
    step_orders = sorted([s.step_order for s in protocol.steps])
    if step_orders != list(range(1, len(protocol.steps) + 1)):
        raise ValueError("Steps must have sequential order (1, 2, 3, ...)")
    
    protocol.state = ProtocolState.FINAL
    protocol.approved_by_user_id = approved_by_user.id
    protocol.effective_start_date = effective_date or date.today()
    protocol.save()
    
    logger.info(f"Approved template: {protocol.protocol_name}")
    return protocol
```

#### 3. Create Instance (Template → Assignment)

```python
def create_protocol_instance(
    template_id: int,
    fermentation_id: int,
    created_by_user: User,
    customizations: Optional[List[StepCustomization]] = None
) -> FermentationProtocol:
    """
    Winemaker: Copy template and optionally customize for specific fermentation.
    
    Customizations allowed BEFORE fermentation starts:
    - Skip a step
    - Modify timing windows
    - Add notes to steps
    
    NOT allowed:
    - Add/remove entire steps (must use different template)
    - Change criticality (that's a template issue)
    """
    
    template = FermentationProtocol.get(id=template_id)
    fermentation = Fermentation.get(id=fermentation_id)
    
    # Only FINAL templates can be used
    if template.state != ProtocolState.FINAL:
        raise ValueError(f"Template must be FINAL, current state: {template.state}")
    
    # Authorization: winemaker+ can assign
    if created_by_user.role not in [UserRole.ADMIN, UserRole.WINEMAKER]:
        raise PermissionError("Only winemakers/admins can assign protocols")
    
    # Create instance (copy of template)
    instance = FermentationProtocol.create(
        winery_id=template.winery_id,
        varietal_code=template.varietal_code,
        varietal_name=template.varietal_name,
        color=template.color,
        version=template.version,
        protocol_name=f"{template.varietal_name} v{template.version} - {fermentation.batch_name}",
        expected_duration_days=template.expected_duration_days,
        is_template=False,
        template_id=template.id,  # Link back to parent
        template_version=template.version,
        state=ProtocolState.FINAL,  # Instance starts in FINAL (ready to use)
        created_by_user_id=created_by_user.id
    )
    
    # Copy all steps from template
    for template_step in template.steps:
        step_copy = ProtocolStep.create(
            protocol_id=instance.id,
            step_order=template_step.step_order,
            step_type=template_step.step_type,
            description=template_step.description,
            expected_day=template_step.expected_day,
            tolerance_hours=template_step.tolerance_hours,
            is_critical=template_step.is_critical,
            criticality_score=template_step.criticality_score,
            # ... copy all fields
        )
        
        # Track original step
        step_copy.template_step_id = template_step.id
        step_copy.save()
    
    # Apply customizations if provided
    if customizations:
        for customization in customizations:
            apply_step_customization(instance.id, customization)
            
            # Log change
            ProtocolChange.create(
                instance_id=instance.id,
                change_type=customization.type,
                step_id=customization.step_id,
                old_value=customization.old_value,
                new_value=customization.new_value,
                reason=customization.reason
            )
    
    # Link to fermentation
    ProtocolExecution.create(
        fermentation_id=fermentation_id,
        protocol_id=instance.id,
        winery_id=fermentation.winery_id,
        start_date=fermentation.start_date,  # Will be set when fermentation actually starts
        status=ProtocolExecutionStatus.NOT_STARTED
    )
    
    logger.info(f"Created protocol instance from template {template.id}")
    return instance
```

#### 4. Customize Steps (Before Execution)

```python
def apply_step_customization(
    protocol_instance_id: int,
    customization: StepCustomization,
    user: User
) -> ProtocolStep:
    """
    Winemaker: Modify specific step before fermentation execution begins.
    """
    
    protocol = FermentationProtocol.get(id=protocol_instance_id)
    step = ProtocolStep.get(id=customization.step_id)
    
    # Only instances can be customized (not templates)
    if protocol.is_template:
        raise ValueError("Cannot customize master templates")
    
    # Only before execution starts
    execution = ProtocolExecution.get(protocol_id=protocol.id)
    if execution.status != ProtocolExecutionStatus.NOT_STARTED:
        raise ValueError("Cannot customize after execution starts")
    
    # Allowed customizations
    if customization.type == "TOLERANCE_ADJUSTMENT":
        # ±6 hours → ±8 hours (more lenient)
        old_tol = step.tolerance_hours
        step.tolerance_hours = customization.new_value
        
        ProtocolChange.create(
            instance_id=protocol_instance_id,
            change_type="TOLERANCE_ADJUSTMENT",
            step_id=step.id,
            old_value=old_tol,
            new_value=customization.new_value,
            reason=customization.reason or "Adjusted based on winery experience"
        )
    
    elif customization.type == "TIMING_ADJUSTMENT":
        # Day 5 → Day 6 (push back timing)
        old_day = step.expected_day
        step.expected_day = customization.new_value
        
        ProtocolChange.create(
            instance_id=protocol_instance_id,
            change_type="TIMING_ADJUSTMENT",
            step_id=step.id,
            old_value=old_day,
            new_value=customization.new_value,
            reason=customization.reason or "Adjusted based on fermentation progress"
        )
    
    elif customization.type == "NOTES_ADDITION":
        # Add specific notes to step
        step.notes = (step.notes or "") + f"\n[{user.name}]: {customization.new_value}"
    
    step.save()
    return step
```

#### 5. Create New Version

```python
def create_protocol_version(
    existing_protocol_id: int,
    new_version_number: str,
    changes_description: str,
    created_by_user: User
) -> FermentationProtocol:
    """
    Admin-only: Create new version of existing protocol (e.g., 1.0 → 1.1 or 1.0 → 2.0).
    """
    
    existing = FermentationProtocol.get(id=existing_protocol_id)
    
    if not existing.is_template:
        raise ValueError("Can only version master templates")
    
    # Validate version format
    if not re.match(r"^\d+\.\d+$", new_version_number):
        raise ValueError("Version must be X.Y format")
    
    # Deprecate old version
    existing.state = ProtocolState.DEPRECATED
    existing.effective_end_date = date.today()
    existing.save()
    
    # Create new version as copy
    new_version = FermentationProtocol.create(
        winery_id=existing.winery_id,
        varietal_code=existing.varietal_code,
        varietal_name=existing.varietal_name,
        color=existing.color,
        version=new_version_number,
        protocol_name=f"{existing.varietal_name} {new_version_number}",
        expected_duration_days=existing.expected_duration_days,
        is_template=True,
        state=ProtocolState.DRAFT,
        created_by_user_id=created_by_user.id
    )
    
    # Copy steps from old version
    for old_step in existing.steps:
        ProtocolStep.create(
            protocol_id=new_version.id,
            step_order=old_step.step_order,
            step_type=old_step.step_type,
            description=old_step.description,
            expected_day=old_step.expected_day,
            tolerance_hours=old_step.tolerance_hours,
            is_critical=old_step.is_critical,
            criticality_score=old_step.criticality_score,
            # ... other fields
        )
    
    # Add change note
    ProtocolVersionNote.create(
        old_version_id=existing.id,
        new_version_id=new_version.id,
        change_description=changes_description,
        created_by_user_id=created_by_user.id
    )
    
    logger.info(f"Created new version: {existing.varietal_code} {new_version_number}")
    return new_version
```

---

### API Endpoints

```python
# Templates (Admin-only)
@router.post("/protocol-templates")
async def create_template(template_data: TemplateCreate):
    """Admin-only: Create new master protocol"""
    return create_protocol_template(...)

@router.get("/protocol-templates/{varietal_code}")
async def list_templates(varietal_code: str, winery_id: int):
    """List all versions of a protocol (FINAL and DEPRECATED)"""
    return FermentationProtocol.filter(
        varietal_code=varietal_code,
        is_template=True,
        winery_id=winery_id
    )

@router.post("/protocol-templates/{protocol_id}/approve")
async def approve_template(protocol_id: int, user: User):
    """Admin-only: Move DRAFT → FINAL"""
    return approve_protocol_template(protocol_id, user)

# Instances (Winemaker+)
@router.post("/protocol-instances")
async def assign_protocol(assignment: ProtocolAssignment):
    """Winemaker: Copy template for specific fermentation"""
    return create_protocol_instance(...)

@router.post("/protocol-instances/{instance_id}/customize")
async def customize_step(instance_id: int, customization: StepCustomization):
    """Winemaker: Modify step before execution"""
    return apply_step_customization(...)

@router.post("/protocol-templates/{protocol_id}/version")
async def create_version(protocol_id: int, version_data: VersionCreate):
    """Admin-only: Create new version"""
    return create_protocol_version(...)
```

---

### Schema

```sql
CREATE TABLE fermentation_protocols (
    -- ... existing ...
    state VARCHAR(20) DEFAULT 'DRAFT',  -- DRAFT, FINAL, DEPRECATED
    is_template BOOLEAN DEFAULT true,
    template_id INTEGER,  -- NULL if is_template=true
    template_version VARCHAR(10),
    effective_start_date DATE,
    effective_end_date DATE,
    approved_by_user_id INTEGER,
    -- ... 
    FOREIGN KEY (template_id) REFERENCES fermentation_protocols(id),
    CHECK (is_template OR template_id IS NOT NULL),
    CHECK (state IN ('DRAFT', 'FINAL', 'DEPRECATED'))
);

CREATE TABLE protocol_changes (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL,
    change_type VARCHAR(50),  -- TOLERANCE_ADJUSTMENT, TIMING_ADJUSTMENT, etc.
    step_id INTEGER NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES fermentation_protocols(id),
    FOREIGN KEY (step_id) REFERENCES protocol_steps(id)
);

CREATE INDEX idx_protocols_template ON fermentation_protocols(is_template);
CREATE INDEX idx_protocols_state ON fermentation_protocols(state);
CREATE INDEX idx_changes_instance ON protocol_changes(instance_id);
```

---

## Consequences

### Positive ✅
- **Reuse**: Templates prevent re-entering same steps
- **Governance**: Admin approval prevents bad protocols
- **Flexibility**: Winemakers can customize for specific conditions
- **Versioning**: Track evolution of protocols over time
- **Audit trail**: All changes logged with reason

### Negative ⚠️
- **Complexity**: 3 states (template/instance/execution) to manage
- **User education**: Winemakers need to understand when they can customize

---

## Testing Strategy

```python
def test_create_template():
    """Can create DRAFT template"""
    template = create_protocol_template(...)
    assert template.state == ProtocolState.DRAFT
    assert template.is_template == True

def test_approve_template():
    """DRAFT → FINAL only by admin"""
    approve_protocol_template(template_id, admin_user)
    template = FermentationProtocol.get(id=template_id)
    assert template.state == ProtocolState.FINAL

def test_instance_from_template():
    """Can create instance from FINAL template"""
    instance = create_protocol_instance(template_id, fermentation_id, user)
    assert instance.is_template == False
    assert instance.template_id == template_id
    assert len(instance.steps) == len(template.steps)

def test_cannot_customize_after_start():
    """Cannot customize after execution starts"""
    execution.status = ProtocolExecutionStatus.ACTIVE
    with pytest.raises(ValueError):
        apply_step_customization(...)
```

