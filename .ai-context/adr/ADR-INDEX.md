# Architecture Decision Records (ADRs) - Index

**Wine Fermentation System**  
**Last Update:** November 15, 2025

---

## 📋 ADR Summary

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| **[ADR-001](./ADR-001-fruit-origin-model-implementation/ADR-001-origin-model.md)** | Fruit Origin Model | ✅ Implemented | 2025-09-25 | High |
| **[ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)** | Repository Architecture | ✅ Implemented | 2025-09-25 | High |
| **[ADR-003](./ADR-003-repository-interface-refactoring.md)** | Repository Separation of Concerns | ✅ Implemented | 2025-10-04 | Medium |
| **[ADR-004](./ADR-004-harvest-module-consolidation.md)** | Harvest Module Consolidation | ✅ Implemented | 2025-10-05 | High |
| **[ADR-005](./ADR-005-service-layer-interfaces.md)** | Service Layer Interfaces & Type Safety | ✅ Implemented | 2025-10-11 | High |
| **[ADR-006](./ADR-006-api-layer-design.md)** | API Layer Design & FastAPI Integration | ✅ Partially Implemented | 2025-11-15 | High |
| **[ADR-007](./ADR-007-auth-module-design.md)** | Authentication Module (Shared Infrastructure) | ✅ Implemented | 2025-11-04 | Critical |

**Legend:**
- ✅ **Implemented** - Fully implemented with tests passing
- 🚀 **Ready** - Prerequisites met, ready for implementation
- 🔄 **In Progress** - Implementation ongoing
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
**Status:** ✅ **Partially Implemented** (Nov 15, 2025)  
**Impact:** Exposes fermentation functionality via HTTP  
**Key Points:**
- **Phases 1-3 Complete**: Core endpoints implemented
  - 2 fermentation endpoints (POST create, GET by ID)
  - 4 sample endpoints (POST, GET list, GET by ID, GET latest)
- **Tests**: 57 API tests passing (16 schema + 29 fermentation + 12 sample)
- Real PostgreSQL database integration ✅
- JWT authentication with shared Auth module ✅
- Multi-tenancy enforcement (winery_id filtering) ✅
- Pydantic v2 for request/response DTOs ✅
- Error handling with proper HTTP status codes ✅
- **Remaining**: 12 additional endpoints (GET list, PATCH, DELETE, etc.)
- **Branch**: feature/fermentation-api-layer

### ADR-007: Authentication Module (Shared Infrastructure)
**Decision:** JWT-based auth in src/shared/auth/ with User entity, role-based authorization  
**Status:** ✅ **Implemented & Production Ready** (Nov 4, 2025 | Fixed Nov 15, 2025)  
**Impact:** Unblocks all API layers, enforces multi-tenancy  
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
- ✅ API Layer (Phases 1-3): Core endpoints with real database
- ✅ Total: **414 tests passing (100%)**
  - Fermentation: 251 tests (173 unit + 69 API + 9 integration)
  - Auth: 163 unit tests

**Current Phase:**
- 🔄 **ADR-006 Phase 4**: Additional API endpoints (GET list, PATCH, DELETE)
- Branch: feature/fermentation-api-layer (commit 6441929)

**Recent Achievements (Nov 15, 2025):**
- ✅ Phase 3 Sample API complete (12 tests)
- ✅ Auth module circular dependency fixed
- ✅ All unit tests passing (100% coverage)
- ✅ Real PostgreSQL integration working
- ✅ JWT authentication integrated in API

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
