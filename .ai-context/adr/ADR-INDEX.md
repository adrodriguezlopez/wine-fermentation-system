# Architecture Decision Records (ADRs) - Index

**Wine Fermentation System**  
**Última actualización:** 2025-10-05

Este documento proporciona un índice de todos los ADRs del proyecto para fácil navegación y comprensión del historial de decisiones arquitectónicas.

---

## 📋 ADR Summary Table

| ADR | Title | Status | Date | Impact | Related Docs |
|-----|-------|--------|------|--------|--------------|
| **[ADR-001](./ADR-001-folder-structure.md)** | Folder Structure | ⚠️ Outdated | - | Low | ⚠️ Ver nota de actualización |
| **[ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)** | Repository Architecture | 🔄 In Progress | 2025-09-25 | High | ARCHITECTURAL_GUIDELINES.md |
| **[ADR-003](./ADR-003-repository-interface-refactoring.md)** | Repository Interface Refactoring | ✅ Implemented | 2025-10-04 | Medium | Fixes circular imports |
| **[ADR-004](./ADR-004-harvest-module-consolidation.md)** | Harvest Module Consolidation & SQLAlchemy Fix | ✅ Implemented | 2025-10-05 | High | ARCHITECTURAL_GUIDELINES.md, MODULE_CONTEXTS |

**Legend:**
- ✅ **Implemented:** Decision fully implemented and verified
- 🔄 **In Progress:** Decision approved, implementation ongoing
- ⚠️ **Outdated:** Information superseded by later ADRs (kept for historical context)

---

## 📚 ADR Details

### ADR-001: Folder Structure ⚠️

**Status:** Outdated (Historical Reference)  
**Original Purpose:** Define folder structure for DDD modules  
**Why Outdated:** Shows `fruit_origin` as subdomain **within** fermentation, but it's now a separate top-level module

**Key Updates:**
- `fruit_origin/` is now a **separate module** under `src/modules/fruit_origin/`
- `winery/` is now a **separate module** under `src/modules/winery/`
- `harvest/` module was **eliminated** (duplicate of fruit_origin)

**See Instead:** 
- [PROJECT_STRUCTURE_MAP.md](../PROJECT_STRUCTURE_MAP.md) - Current structure
- [ADR-004](./ADR-004-harvest-module-consolidation.md) - Module consolidation rationale

---

### ADR-002: Repository Architecture

**Status:** 🔄 In Progress  
**Date:** 2025-09-25  
**Impact:** High (Foundation for all repository implementations)

**Key Decisions:**
1. **Ports & Adapters:** Each aggregate defines its own interface
2. **BaseRepository:** Infrastructure helper for session, errors, soft-delete
3. **Unit of Work:** Async context manager for transactions
4. **Multi-tenancy:** All queries scoped by `winery_id`
5. **Optimistic Locking:** Version field in Fermentation
6. **Error Mapping:** Database exceptions → Domain exceptions
7. **SOLID Compliance:** Interface-based design with DIP

**Implementation Status:**
- ✅ Error mapping (19 tests passing)
- ✅ Repository interfaces defined
- ✅ FermentationRepository concrete implementation (13 tests passing)
- 🔄 BaseRepository (next phase)
- 🔄 Unit of Work (pending)

**Related Files:**
- `src/modules/fermentation/src/repository_component/errors.py`
- `src/modules/fermentation/src/repository_component/repositories/fermentation_repository.py`
- `src/modules/fermentation/src/domain/repositories/fermentation_repository_interface.py`

**Related ADRs:**
- [ADR-003](./ADR-003-repository-interface-refactoring.md) - Interface sync & circular import fixes
- [ADR-004](./ADR-004-harvest-module-consolidation.md) - SQLAlchemy patterns for repositories

---

### ADR-003: Repository Interface Refactoring

**Status:** ✅ Implemented  
**Date:** 2025-10-04  
**Impact:** Medium (Fixes technical debt)

**Problem:**
- Circular imports in entity files
- Repository interface out of sync with SQLAlchemy model
- Inconsistent import patterns

**Solutions Implemented:**
1. **Proper TYPE_CHECKING usage:** Conditional imports for type hints
2. **Canonical entity locations:** Single source of truth for each entity
3. **Interface synchronization:** Repository methods match SQLAlchemy model exactly
4. **Import cleanup:** Relative imports from canonical locations

**Results:**
- ✅ 95/95 tests passing (at time of ADR-003)
- ✅ No circular import errors
- ✅ Repository interface reflects reality

**Files Modified:**
- Entity imports in `src/modules/fermentation/src/domain/entities/`
- Repository interface in `src/modules/fermentation/src/domain/repositories/`

**Related ADRs:**
- [ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md) - Repository foundation
- [ADR-004](./ADR-004-harvest-module-consolidation.md) - Further import improvements

---

### ADR-004: Harvest Module Consolidation & SQLAlchemy Registry Fix ⭐

**Status:** ✅ Implemented  
**Date:** 2025-10-05  
**Impact:** High (Major architectural cleanup + critical SQLAlchemy patterns)

**Problem 1: Module Duplication**
- `src/modules/harvest/` had `HarvestLot` with 5 basic fields
- `src/modules/fruit_origin/` had `HarvestLot` with 19 complete traceability fields
- Architectural confusion about correct location

**Problem 2: SQLAlchemy Registry Conflicts**
- Error: "Multiple classes found for path 'BaseSample'"
- Caused by: Short paths in relationships, single-table inheritance issues, inconsistent imports

**Decisions Made:**

**1. Module Consolidation (Harvest → fruit_origin)**
- ✅ Eliminated `src/modules/harvest/` module
- ✅ Consolidated to `src/modules/fruit_origin/` with full 19-field HarvestLot
- ✅ Proper bounded context: fruit_origin = Vineyard → VineyardBlock → HarvestLot

**2. SQLAlchemy Patterns (CRITICAL):**
- ✅ **Fully-Qualified Paths:** Use complete module paths in `relationship()`
- ✅ **Unidirectional Relationships:** Use `viewonly=True` for single-table inheritance
- ✅ **Consistent Imports:** Always `from src.shared.infra.orm.base_entity import BaseEntity`
- ✅ **Test Compatibility:** Add `extend_existing=True` in `__table_args__`
- ✅ **Transaction Management:** Use `flush()` not `commit()` in test fixtures

**Results:**
- ✅ 103/103 tests passing (102 unit + 1 integration)
- ✅ 9 database tables created successfully
- ✅ 0 SQLAlchemy registry conflicts
- ✅ harvest/ module eliminated, 0 broken references

**Impact on Other Documents:**
- [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md) - New section: "🗄️ SQLAlchemy Import Best Practices"
- [PROJECT_STRUCTURE_MAP.md](../PROJECT_STRUCTURE_MAP.md) - Updated module structure, database schema
- [fruit_origin/module-context.md](../fruit_origin/module-context.md) - Complete bounded context documentation
- [winery/module-context.md](../winery/module-context.md) - Multi-tenancy root documentation
- [fermentation/module-context.md](../fermentation/module-context.md) - Cross-module dependencies

**Files Modified (8):**
1. `tests/integration/conftest.py` - Updated imports, new fixtures
2. `recreate_test_tables.py` - Updated imports
3. 3 debug scripts - Updated imports
4. `fruit_origin/entities/harvest_lot.py` - Fixed import + extend_existing
5. `fruit_origin/entities/vineyard.py` - Fixed import + extend_existing
6. `fruit_origin/entities/vineyard_block.py` - Fixed import + extend_existing

**Files Deleted:**
- `src/modules/harvest/` (entire module)

**New Entities Added to System:**
- `Vineyard` (fruit_origin)
- `VineyardBlock` (fruit_origin)
- `HarvestLot` (fruit_origin - enhanced from 5 to 19 fields)

---

## 🔗 Cross-Document References

### For Module Architecture:
- **Start:** [PROJECT_STRUCTURE_MAP.md](../PROJECT_STRUCTURE_MAP.md)
- **Principles:** [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md)
- **Bounded Contexts:** 
  - [fermentation/module-context.md](../../src/modules/fermentation/.ai-context/module-context.md)
  - [fruit_origin/module-context.md](../../src/modules/fruit_origin/.ai-context/module-context.md)
  - [winery/module-context.md](../../src/modules/winery/.ai-context/module-context.md)

### For Implementation Patterns:
- **SQLAlchemy:** [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md) - Section: "🗄️ SQLAlchemy Import Best Practices"
- **Repositories:** [ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)
- **Error Handling:** `src/modules/fermentation/src/repository_component/errors.py`

### For Historical Context:
- **Folder Structure Evolution:** [ADR-001](./ADR-001-folder-structure.md) → [ADR-004](./ADR-004-harvest-module-consolidation.md)
- **Import Patterns Evolution:** [ADR-003](./ADR-003-repository-interface-refactoring.md) → [ADR-004](./ADR-004-harvest-module-consolidation.md)

---

## 📈 ADR Evolution Timeline

```
2025-09-25: ADR-002 - Repository Architecture (Foundation)
              ↓
              ├─ Defined Ports & Adapters pattern
              ├─ Established error mapping strategy
              └─ Multi-tenancy requirements

2025-10-04: ADR-003 - Repository Interface Refactoring
              ↓
              ├─ Fixed circular imports
              ├─ Synchronized interfaces
              └─ Canonical entity locations

2025-10-05: ADR-004 - Harvest Consolidation & SQLAlchemy Fix ⭐
              ↓
              ├─ Eliminated duplicate harvest/ module
              ├─ Established SQLAlchemy best practices
              ├─ Fixed registry conflicts (CRITICAL)
              ├─ Created module contexts (fermentation, fruit_origin, winery)
              └─ Current state: 103 tests passing, clean architecture
```

---

## 🚀 Next ADRs (Anticipated)

Based on current development trajectory, future ADRs may cover:

1. **ADR-005: Unit of Work Pattern** (Expected)
   - Implementation of async transaction management
   - Cross-repository atomic operations
   - Rollback strategies

2. **ADR-006: API Layer Architecture** (Future)
   - FastAPI endpoint organization
   - Request/Response DTOs
   - Authentication & Authorization

3. **ADR-007: Read Model Optimization** (Future)
   - Reporting queries separate from domain
   - Denormalization strategies
   - Performance optimization

---

## 📝 How to Write a New ADR

When documenting a new architectural decision:

1. **Use the template:** `.ai-context/adr/ADR-template-light.md` or `ADR-template.md`
2. **Number sequentially:** Next ADR = ADR-005
3. **Include sections:**
   - Context (Why this decision is needed)
   - Decision (What was decided)
   - Consequences (Positive & Negative impacts)
   - Verification (How to validate it's implemented correctly)
4. **Cross-reference:** Link to related ADRs and documents
5. **Update this index:** Add entry to summary table and details section
6. **Update related docs:** PROJECT_STRUCTURE_MAP.md, ARCHITECTURAL_GUIDELINES.md, etc.

**Example ADR lifecycle:**
```
Problem Identified
  ↓
ADR Proposed (Status: Proposed)
  ↓
Team Review & Discussion
  ↓
ADR Approved (Status: In Progress)
  ↓
Implementation & Testing
  ↓
ADR Completed (Status: Implemented)
  ↓
Update cross-references in other docs
```

---

## 📚 ADR Best Practices

1. **Immutable:** ADRs are records - don't edit historical decisions
2. **Supersede, don't delete:** If decision changes, create new ADR that supersedes old one
3. **Cross-reference:** Always link related ADRs
4. **Consequences matter:** Document both positive AND negative impacts
5. **Verification:** Include acceptance criteria or test status
6. **Date stamp:** Always include date of decision
7. **Context first:** Explain WHY before WHAT

---

**Maintained by:** Development Team  
**Last updated:** 2025-10-05  
**Next review:** After ADR-005 creation
