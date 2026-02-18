# Protocol Semantic Versioning & Migration Guide

**Status**: Reference Documentation  
**Date**: February 12, 2026  
**Related ADR**: ADR-035 (Protocol Data Model), ADR-039 (Protocol Template Management)

---

## Table of Contents

1. [Versioning Strategy](#versioning-strategy)
2. [Version Format](#version-format)
3. [Backwards Compatibility](#backwards-compatibility)
4. [Migration Paths](#migration-paths)
5. [Version Management in Code](#version-management-in-code)
6. [Examples](#examples)

---

## Versioning Strategy

Protocol versions follow **semantic versioning** principles adapted for wine fermentation protocols:

- **MAJOR version**: Fundamental changes to protocol structure or winemaking approach that may affect fermentation outcome
- **MINOR version**: Additive changes that improve protocol without breaking existing implementations
- **No PATCH version**: Protocols use X.Y format only; step-level adjustments are MINOR bumps

### When to Bump Versions

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| New step added mid-process | MINOR | Add optional oak aging step → v1.1 |
| Temperature range tightened | MINOR | Change from ±2°C to ±1°C tolerance |
| Complete process redesign | MAJOR | Switch cold soak strategy entirely → v2.0 |
| Critical timing adjustment | MINOR | Move H₂S check from day 5 to day 3 |
| Bug fix in step description | MINOR | Clarify SO₂ dosage calculation |
| Experimental alternative path | MINOR | Optional MLF inoculation timing |

---

## Version Format

### Schema: `X.Y`

```
FermentationProtocol.version: "1.0"  # String stored in database
FermentationProtocol.version: "1.5"  # One minor update
FermentationProtocol.version: "2.1"  # Major redesign with one minor revision
```

### Validation

Protocol versions are validated via regex in DTOs:

```python
# From protocol_dtos.py
validate_semantic_version(version: str) -> bool
# Regex: ^\d+\.\d+$
# Valid: "1.0", "1.5", "2.0", "10.15"
# Invalid: "1", "1.0.0", "1.x", "v1.0"
```

### Version Uniqueness Constraint

Database enforces single definition per combination:

```sql
UNIQUE(winery_id, varietal_code, version)
```

This means:
- ✅ R&G Pinot Noir v1.0 and v1.1 can both exist
- ✅ R&G Pinot Noir v1.0 and Napa Family Pinot Noir v1.0 can both exist
- ❌ R&G Pinot Noir v1.0 cannot exist twice

---

## Backwards Compatibility

### Active Version Strategy

Only **one protocol version is "active" at a time** per winery/varietal:

```python
FermentationProtocol.is_active: bool  # Only one TRUE per (winery_id, varietal_code)
```

### Migration Timeline

```
Old Protocol (v1.0)     New Protocol (v1.1)     Timeline
├─ is_active = FALSE ◄── is_active = TRUE      When upgrade happens
├─ New executions: BLOCKED
└─ Existing executions: CONTINUE with v1.0     No retroactive changes
```

### Step-Level Compatibility

When protocol is upgraded mid-fermentation:

```
ProtocolExecution
├─ protocol_id: points to ORIGINAL version (v1.0)
├─ fermentation_id: continues with original steps
├─ status: continues executing v1.0 steps
└─ NOTE: New fermentations use protocol_id of v1.1
```

This ensures:
- ✅ Current fermentations finish with their protocol version
- ✅ New fermentations use latest protocol
- ✅ No retroactive step changes during active fermentation

---

## Migration Paths

### Scenario 1: Minor Update (v1.0 → v1.1)

**Change**: Add optional monitoring step

**Process**:

```sql
-- 1. Create new protocol row
INSERT INTO fermentation_protocols 
  (winery_id, varietal_code, version, is_active, ...)
VALUES (1, 'PN', '1.1', false, ...);

-- 2. Copy steps from v1.0 to v1.1
INSERT INTO protocol_steps (protocol_id, step_order, ...)
SELECT <new_v1.1_id>, step_order, ...
FROM protocol_steps
WHERE protocol_id = <v1.0_id>;

-- 3. Add new step to v1.1
INSERT INTO protocol_steps (protocol_id, step_order, ...)
VALUES (<new_v1.1_id>, 15, 'OPTIONAL_MONITORING', ...);

-- 4. Deactivate old, activate new
UPDATE fermentation_protocols 
SET is_active = CASE 
  WHEN version = '1.0' THEN false
  WHEN version = '1.1' THEN true
END
WHERE winery_id = 1 AND varietal_code = 'PN';

-- 5. Document in audit log (manual)
-- "Upgraded from v1.0→v1.1: Added optional monitoring step"
```

**Existing Executions**: Continue with v1.0 steps, unaffected

**New Executions**: Use v1.1 with new step included

---

### Scenario 2: Major Update (v1.x → v2.0)

**Change**: Completely redesign temperature strategy

**Process**: Same as Scenario 1, but:

```python
# ProtocolCreate DTO validation
new_protocol = ProtocolCreate(
    winery_id=1,
    varietal_code="PN",
    version="2.0",  # Major bump
    protocol_name="Pinot Noir - Temperature Optimized",
    description="Complete redesign for precision temperature control",
    is_active=False,  # Pre-approval phase
)

# Winemaker reviews v2.0 specification
# Confirms with: is_active=True in next update
```

**Considerations**:

- Document breaking changes in `protocol_name` or `description`
- Provide side-by-side comparison of v1.x vs v2.0 steps
- Consider training requirement before activation
- Set activation date, don't activate immediately

---

### Scenario 3: Rollback (v1.1 → v1.0)

**Emergency only** - If v1.1 proves problematic:

```python
# Deactivate v1.1, reactivate v1.0
protocol_repository.update_fermentation_protocol(
    protocol_id=protocol_v1_1_id,
    updates={"is_active": False}
)

protocol_repository.update_fermentation_protocol(
    protocol_id=protocol_v1_0_id,
    updates={"is_active": True}
)

# New fermentations use v1.0
# In-progress v1.1 executions continue (no change retroactively)
```

---

## Version Management in Code

### Creating Versioned Protocols

```python
# From phase 2 API layer (future)
@router.post("/protocols")
async def create_protocol(
    req: ProtocolCreate,
    session: AsyncSession
) -> ProtocolResponse:
    # ProtocolCreate validates version format (X.Y)
    if not validate_semantic_version(req.version):
        raise ValueError(f"Invalid version: {req.version}")
    
    # Check uniqueness: (winery_id, varietal_code, version)
    existing = await protocol_repository.get_by_winery_varietal_version(
        req.winery_id, 
        req.varietal_code, 
        req.version
    )
    if existing:
        raise ConflictError(f"Protocol v{req.version} already exists")
    
    # Create new protocol
    protocol = await protocol_repository.create(
        fermentation_protocol=FermentationProtocol(
            winery_id=req.winery_id,
            varietal_code=req.varietal_code,
            version=req.version,
            protocol_name=req.protocol_name,
            is_active=False,  # Start inactive
        )
    )
    
    return ProtocolResponse.from_entity(protocol)
```

### Activating a Protocol Version

```python
@router.patch("/protocols/{protocol_id}/activate")
async def activate_protocol(
    protocol_id: int,
    session: AsyncSession
) -> ProtocolResponse:
    # Get the protocol to activate
    protocol = await protocol_repository.get_by_id(protocol_id)
    if not protocol:
        raise NotFoundError(f"Protocol {protocol_id} not found")
    
    # Deactivate all other versions of same (winery, varietal)
    await protocol_repository.deactivate_by_winery_varietal(
        winery_id=protocol.winery_id,
        varietal_code=protocol.varietal_code
    )
    
    # Activate this version
    protocol.is_active = True
    await protocol_repository.update(protocol)
    
    # Log activation event
    # audit_service.log_protocol_activated(protocol)
    
    return ProtocolResponse.from_entity(protocol)
```

### Querying Current Protocol

```python
# Get active protocol for a winery/varietal
protocol = await protocol_repository.get_active_by_winery_varietal(
    winery_id=1,
    varietal_code="PN"
)
# Returns: v1.1 if is_active=True
# Returns: None if no version is active (error state)

# Get all versions for comparison
versions = await protocol_repository.list_by_winery_varietal(
    winery_id=1,
    varietal_code="PN"
)
# Returns: [v1.0 (inactive), v1.1 (active), v2.0 (inactive)]
```

---

## Examples

### Example 1: Pinot Noir Protocol Versioning

**R&G Pinot Noir History**:

```
Version 1.0 (Active 2023-2024)
├─ Status: Archived
├─ Yeast: Rc212 only
├─ H₂S check: Day 5
└─ Duration: 18 days

Version 1.1 (Active 2024-2025)  ◄── CURRENT ACTIVE
├─ Updated: Added optional oak monitoring
├─ Yeast: Rc212 or EC1118
├─ H₂S check: Day 3 (earlier)
├─ Duration: 20 days
└─ Added step: OPTIONAL_OAK_MONITORING (day 15)

Version 2.0 (Pre-approval)
├─ Status: Under review
├─ Redesign: Temperature precision approach
├─ Estimated activation: 2026 harvest season
└─ Breaking change: Requires new monitoring equipment
```

### Example 2: Migration from 1.0 to 1.1

**Pinot Noir Fermentations**:

```
Fermentation A (Started with v1.0)
├─ Started: Jan 1, 2026
├─ protocol_id: protocol_v1.0
├─ Steps: Follow v1.0 (18 days, H₂S on day 5)
├─ Migration event: Jan 15 (v1.0→v1.1 released)
└─ Action: NONE - continues with v1.0 until completion

Fermentation B (Starts after v1.1 activated)
├─ Started: Jan 16, 2026
├─ protocol_id: protocol_v1.1
├─ Steps: Follow v1.1 (20 days, H₂S on day 3, +monitoring)
└─ Includes: New oak monitoring step at day 15
```

### Example 3: Database Uniqueness Constraint

```sql
-- Valid: Multiple versions of same wine
INSERT INTO fermentation_protocols (winery_id, varietal_code, version, is_active)
VALUES 
  (1, 'PN', '1.0', FALSE),  ✓ OK
  (1, 'PN', '1.1', TRUE),   ✓ OK
  (1, 'PN', '2.0', FALSE);  ✓ OK

-- Valid: Same version, different winery
INSERT INTO fermentation_protocols (winery_id, varietal_code, version, is_active)
VALUES 
  (1, 'PN', '1.0', FALSE),  -- R&G Pinot Noir v1.0
  (2, 'PN', '1.0', TRUE);   ✓ OK - Different winery

-- Invalid: Duplicate version
INSERT INTO fermentation_protocols (winery_id, varietal_code, version, is_active)
VALUES 
  (1, 'PN', '1.1', FALSE);  ✗ CONSTRAINT VIOLATION - v1.1 already exists for (winery=1, varietal='PN')
```

---

## Decision Table: When to Create New Version

| Question | Yes = New Version | No = Keep Current |
|----------|------------------|-------------------|
| Does change affect fermentation timing? | MINOR bump | Skip |
| Does change require new equipment? | MAJOR bump | MINOR bump |
| Can existing fermentation continue unchanged? | Keep v1, create v2 | Update current version |
| Is this a bug fix? | MINOR bump | Update current version |
| Was this already known limitation? | Document in v description | MAJOR bump next review |
| Do winemakers need retraining? | MAJOR bump, note in docs | MINOR bump |

---

## Reference: ProtocolCreate DTO Validation

```python
@dataclass
class ProtocolCreate:
    winery_id: int
    varietal_code: str
    protocol_name: str
    version: str  # Validated: regex ^\d+\.\d+$
    expected_duration_days: int
    description: Optional[str] = None
    is_active: bool = False
    
    def __post_init__(self):
        # Validate version format
        if not validate_semantic_version(self.version):
            raise ValueError(
                f"Version must be X.Y format (e.g., '1.0'). Got: {self.version}"
            )
        
        # Validate positive duration
        if not validate_positive_int(self.expected_duration_days):
            raise ValueError(
                f"Expected duration must be > 0. Got: {self.expected_duration_days}"
            )
        
        # Validate code format
        if not (1 <= len(self.varietal_code) <= 4):
            raise ValueError(
                f"Varietal code must be 1-4 characters. Got: {self.varietal_code}"
            )
```

---

## Next Steps

1. **Phase 2 API**: Implement versioning endpoints
   - POST /protocols - Create new version
   - PATCH /protocols/{id}/activate - Activate version
   - GET /protocols - List all versions with status

2. **Admin Interface**: Add version comparison view
   - Side-by-side step comparison
   - Version history timeline
   - Activation approval workflow

3. **Analytics**: Track adoption curves
   - When did v1.1 adoption happen?
   - How many fermentations per version?
   - Version rollout metrics

---

**Document Version**: 1.0  
**Last Updated**: February 12, 2026  
**Owner**: Protocol Engine Development Team
