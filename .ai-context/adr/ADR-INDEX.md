# Architecture Decision Records (ADRs) - Index

**Wine Fermentation System**  
**Last Update:** November 25, 2025

---

## 📋 ADR Summary

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| **[ADR-001](./ADR-001-fruit-origin-model-implementation/ADR-001-origin-model.md)** | Fruit Origin Model | ✅ Implemented | 2025-09-25 | High |
| **[ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)** | Repository Architecture | ✅ Implemented | 2025-09-25 | High |
| **[ADR-003](./ADR-003-repository-interface-refactoring.md)** | Repository Separation of Concerns | ✅ Implemented | 2025-10-04 | Medium |
| **[ADR-004](./ADR-004-harvest-module-consolidation.md)** | Harvest Module Consolidation | ✅ Implemented | 2025-10-05 | High |
| **[ADR-005](./ADR-005-service-layer-interfaces.md)** | Service Layer Interfaces & Type Safety | ✅ Implemented | 2025-10-11 | High |
| **[ADR-006](./ADR-006-api-layer-design.md)** | API Layer Design & FastAPI Integration | ✅ Implemented | 2025-11-15 | High |
| **[ADR-007](./ADR-007-auth-module-design.md)** | Authentication Module (Shared Infrastructure) | ✅ Implemented | 2025-11-04 | Critical |
| **[ADR-008](./ADR-008-centralized-error-handling.md)** | Centralized Error Handling for API Layer | ✅ Implemented | 2025-11-15 | Medium |
| **[ADR-009](./ADR-009-missing-repositories-implementation.md)** | Missing Repositories Implementation | 📋 Proposed | 2025-11-25 | High |

**Legend:**
- ✅ **Implemented** - Fully implemented with tests passing
- 🚀 **Ready** - Prerequisites met, ready for implementation
- 🔄 **In Progress** - Implementation ongoing
- 📋 **Proposed** - Under review, not yet approved
- ⚠️ **Superseded** - Replaced by newer decision

---

## 📚 Quick Reference

### ADR-001: Fruit Origin Model
**Decision:** Hierarchy Winery → Vineyard → VineyardBlock → HarvestLot  
**Status:** ✅ Implemented  
**Impact:** Enables full traceability from wine to vineyard  
**Key Points:**
- Multi-tenancy prepared (MVP single-tenant)
- Business rules enforced (mass totals, same winery)
- `FermentationLotSource` association table

### ADR-002: Repository Architecture
**Decision:** Ports & Adapters with BaseRepository helper  
**Status:** ✅ Implemented (110 tests passing)  
**Impact:** Foundation for all data access  
**Key Points:**
- Interface-based design (DIP)
- Multi-tenancy scoping
- Error mapping (DB → Domain)
- Soft-delete support

### ADR-003: Repository Separation of Concerns
**Decision:** FermentationRepository ≠ SampleRepository  
**Status:** ✅ Implemented (102 tests passing)  
**Impact:** SRP compliance, cleaner architecture  
**Key Points:**
- Removed samples logic from FermentationRepository
- Fixed circular imports
- Eliminated code duplication
- One repository = one aggregate root

### ADR-004: Harvest Module Consolidation
**Decision:** Consolidate `harvest/` into `fruit_origin/`  
**Status:** ✅ Implemented  
**Impact:** Cleaner bounded context, no duplication  
**Key Points:**
- Eliminated duplicate HarvestLot entity
- SQLAlchemy registry fix (fully-qualified paths)
- Unidirectional relationships with inheritance
- flush() vs commit() in tests

### ADR-005: Service Layer Interfaces & Type Safety
**Decision:** Type-safe service interfaces, DTOs → Entities  
**Status:** ✅ Implemented (115 tests passing)  
**Impact:** Type safety, Clean Architecture, SOLID  
**Key Points:**
- FermentationService: 7 methods (33 tests)
- SampleService: 6 methods (27 tests)
- FermentationValidator extracted (SRP)
- Multi-tenancy enforced
- NO more Dict[str, Any]

### ADR-006: API Layer Design & FastAPI Integration
**Decision:** REST API with FastAPI, JWT auth, Pydantic DTOs  
**Status:** ✅ **FULLY IMPLEMENTED** (Nov 15, 2025)  
**Impact:** Exposes fermentation functionality via HTTP  
**Key Points:**
- **All Phases Complete**: All 18 endpoints implemented (100%)
  - 10 fermentation endpoints (create, get, list, update, delete, validate, timeline, stats, etc.)
  - 8 sample endpoints (create, get, list, latest, types, timerange, validate, delete)
- **Tests**: 90 API tests passing (100% coverage)
- Real PostgreSQL database integration ✅
- JWT authentication with shared Auth module ✅
- Multi-tenancy enforcement (winery_id filtering) ✅
- Pydantic v2 for request/response DTOs ✅
- **Centralized error handling** with decorator pattern ✅
- **Code quality**: ~410 lines eliminated via refactoring ✅
- **Branch**: feature/fermentation-api-layer (merged to main)

### ADR-007: Authentication Module (Shared Infrastructure)
**Decision:** JWT-based auth in src/shared/auth/ with User entity, role-based authorization  
**Status:** ✅ **Implemented & Production Ready** (Nov 4, 2025 | Fixed Nov 15, 2025)  
**Impact:** Unblocks all API layers, enforces multi-tenancy  

### ADR-008: Centralized Error Handling for API Layer
**Decision:** Use decorator pattern for exception→HTTP mapping  
**Status:** ✅ **Implemented** (Nov 15, 2025)  
**Impact:** Eliminated code duplication, improved maintainability  
**Key Points:**
- **Single decorator**: `@handle_service_errors` wraps all endpoints
- **Code reduction**: ~410 lines of duplicated try/except blocks eliminated
- **Standardized mappings**: NotFoundError→404, ValidationError→422, DuplicateError→409, etc.
- **Refactored**: 17/17 endpoints (100%)
- **Tests**: All 90 API tests passing with new error handling
- **Benefits**: DRY principle, single source of truth, easier maintenance  
**Key Points:**
- User entity with winery_id (multi-tenancy)
- JWT tokens (15min access + 7 days refresh)
- 4 roles: Admin, Winemaker, Operator, Viewer
- FastAPI dependencies (get_current_user, require_role)
- **Test Coverage**: 163 unit tests passing (100%)
- PasswordService (bcrypt), JwtService (PyJWT), AuthService
- Migration completed: User moved from fermentation to shared/auth
- **Critical Fix (Nov 15)**: Removed circular dependencies
  - User→Fermentation relationships commented out
  - Auth module now testable independently
- Successfully integrated in fermentation API endpoints ✅

---

## 📊 Current Status (Nov 15, 2025)

**Implementation Complete:**
- ✅ Domain Layer (Entities, DTOs, Enums, Interfaces)
- ✅ Repository Layer (FermentationRepository + SampleRepository)
- ✅ Service Layer (FermentationService + SampleService + Validators)
- ✅ Auth Module (shared/auth with JWT, RBAC, multi-tenancy)
- ✅ **API Layer (All Phases)**: Complete endpoint suite with real database
- ✅ **Error Handling Refactoring**: Centralized with decorator pattern
- ✅ Total: **272 tests passing (100%)**
  - Fermentation: 272 tests (173 unit + 9 integration + 90 API)
  - Auth: 163 unit tests (separate module)

**Current Phase:**
- ✅ **ADR-006 Phase 4 COMPLETE**: All API endpoints implemented
- ✅ **ADR-008 COMPLETE**: Error handling refactored with decorator pattern
- Branch: feature/fermentation-api-layer (commit 6fa62d5)

**Recent Achievements (Nov 15, 2025):**
- ✅ Phase 4 Complete: All 18 endpoints implemented (10 fermentation + 8 sample)
- ✅ Error Handling Refactored: ~410 lines eliminated via decorator pattern
- ✅ All 90 API tests passing (100% coverage)
- ✅ Code quality improved: DRY principle enforced
- ✅ Documentation updated: ADR-006, ADR-008 (NEW), module-context.md
- ✅ Router exports fixed: samples_router properly registered

**Code Metrics:**
- API endpoints: 18/18 implemented (100%) ✅
- Code reduction: ~410 lines eliminated via refactoring
- Test coverage: 272/272 tests passing (100%)
- Commits: 9 total (incremental commits with clear messages)

---

## 🔗 Related Documentation

- **System Context:** [project-context.md](../project-context.md)
- **Architecture:** [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md)
- **Structure:** [PROJECT_STRUCTURE_MAP.md](../PROJECT_STRUCTURE_MAP.md)
- **Collaboration:** [collaboration-principles.md](../collaboration-principles.md)

---

## 📝 ADR Template Guide

When creating new ADRs, use:
- **[ADR-template-light.md](./ADR-template-light.md)** - For simple decisions (4 sections)
- **[ADR-template.md](./ADR-template.md)** - For complex decisions (11 sections)
- **[ADR-template-selection-guide.md](./ADR-template-selection-guide.md)** - Decision matrix

**Template Rules:**
- Keep ADRs concise (< 200 lines)
- Focus on decisions, not implementation details
- Use Quick Reference for developers
- Update this index when adding new ADRs
