# Test Failure Analysis - ADR-035 Protocol Engine

## Summary
The test suite shows several failures in modules that import Protocol entities:
- Winery Unit Tests: 3 failed
- Fruit Origin Unit Tests: 6 failed  
- Fermentation Unit Tests: 19 failed, 17 errors

## Root Causes Identified

### Issue 1: User Entity Reference in FermentationProtocol
**Problem**: FermentationProtocol references a `User` entity via `created_by_user_id` foreign key, but the User entity is not properly available during SQLAlchemy initialization.

**Error**: 
```
When initializing mapper Mapper[FermentationProtocol(fermentation_protocols)], 
expression 'User' failed to locate a name ('User'). 
If this is a class name, consider adding this relationship() to the class after both dependent classes have been defined.
```

**Location**: `src/modules/fermentation/src/domain/entities/protocol_protocol.py:40-41`
```python
created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
created_by: Mapped[Optional["User"]] = relationship(...)
```

**Why It Fails**:
- `User` is imported only in `TYPE_CHECKING` block (for type hints only)
- At runtime, SQLAlchemy can't find the actual User class to establish the relationship
- This causes a mapper initialization error when any test tries to instantiate FermentationProtocol

**Impact**:
- Winery tests fail when trying to create test data that references protocols
- Fruit Origin tests fail when trying to create vineyards linked to protocols
- Fermentation tests fail when trying to test protocol relationships

### Issue 2: ProtocolStep Mapper Initialization
**Problem**: Similar to Issue 1, ProtocolStep has relationships that fail to initialize properly.

**Error**:
```
Column expression expected for argument 'remote_side'; got <built-in function id>.
```

**Location**: Likely in the relationship definitions within ProtocolStep

### Issue 3: Circular Import Prevention
**Problem**: User entity is in `src.shared.auth.domain.entities`, while FermentationProtocol is in `src.modules.fermentation.src.domain.entities`. When trying to import User at module level, it creates circular dependencies.

**Solution Strategy**:
The code uses `TYPE_CHECKING` to prevent circular imports, but SQLAlchemy ORM needs actual class references at runtime, not just type hints.

## Solutions

### Option A: Remove User Relationship (Recommended for ADR-035 Phase 1)
**Rationale**: 
- Protocol doesn't need to know WHO created it at the ORM level
- Can track creation user in database without ORM relationship
- Simplifies model and avoids cross-module entity dependencies
- Audit trail can be handled at service level

**Changes Required**:
```python
# Remove these lines:
created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
created_by: Mapped[Optional["User"]] = relationship(...)

# Keep a simple user_id for audit (no relationship):
created_by: Mapped[int] = mapped_column(Integer, nullable=False)  # No FK constraint
```

**Pros**:
- Simplest fix
- No circular dependencies
- Follows SOLID principles (entities should be independent)
- Allows Protocol module to not depend on Auth module

**Cons**:
- Lose type safety on the relationship
- Can't directly access user object via protocol.created_by

### Option B: Use String-based Foreign Key (Late Binding)
**Changes**:
```python
from sqlalchemy.orm import relationship

created_by: Mapped[Optional["User"]] = relationship(
    "User",
    foreign_keys="[FermentationProtocol.created_by_user_id]",  # String-based
    lazy="select",
    viewonly=True  # Read-only to avoid update cascade issues
)
```

**Pros**:
- Keeps relationship definition
- Uses SQLAlchemy's deferred resolution

**Cons**:
- Still requires User class to be registered somewhere
- May still cause initialization order issues

### Option C: Use Polymorphic Relationships
**Changes**:
- Create an abstract AuditMixin in shared
- Both User and Protocol inherit from it
- Avoids direct cross-module references

**Pros**:
- More robust architecturally
- Reusable pattern for other modules

**Cons**:
- More complex implementation
- Requires schema changes

## Recommended Action for ADR-035 Phase 1

**Implement Option A**: Remove the User relationship from FermentationProtocol

**Why**:
1. Protocol tests are passing with current simple structure (29/29 ✅)
2. Removing relationship won't break Protocol functionality
3. Other modules can continue with their current logic
4. User tracking can be added in Phase 2 with proper architecture

**Implementation**:
1. Remove `created_by_user_id` foreign key constraint
2. Replace with simple `created_by` integer field (no FK)
3. Update ProtocolExecution and StepCompletion similarly
4. Re-run full test suite
5. Document decision in ADR notes

## Test Results After Each Option

### Current State
- Protocol Unit Tests: ✅ 29/29 PASSING
- Winery Unit Tests: ❌ 3 failed
- Fruit Origin Unit Tests: ❌ 6 failed
- Fermentation Unit Tests: ❌ 19 failed, 17 errors
- **Total**: 878 passing, 28 failing

### Expected After Option A
- Protocol Unit Tests: ✅ 29/29 PASSING
- Winery Unit Tests: ✅ Should fix 3 failures (41 passing)
- Fruit Origin Unit Tests: ✅ Should fix 6 failures (107+ passing)
- Fermentation Unit Tests: ✅ Should fix entity errors
- **Expected Total**: 912+ passing, < 10 failing

## Files Affected
- `src/modules/fermentation/src/domain/entities/protocol_protocol.py`
- `src/modules/fermentation/src/domain/entities/protocol_execution.py`
- `src/modules/fermentation/src/domain/entities/step_completion.py`

## Next Steps
1. Choose and implement recommended solution
2. Re-run full test suite
3. Document decision in ADR-035 Phase 1 completion notes
4. Consider Options B or C for Phase 2 if relationships needed
