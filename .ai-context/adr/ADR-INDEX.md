# Architecture Decision Records (ADRs) - Index

**Wine Fermentation System**  
**Last Update:** November 4, 2025

---

## 📋 ADR Summary

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| **[ADR-001](./ADR-001-fruit-origin-model-implementation/ADR-001-origin-model.md)** | Fruit Origin Model | ✅ Implemented | 2025-09-25 | High |
| **[ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)** | Repository Architecture | ✅ Implemented | 2025-09-25 | High |
| **[ADR-003](./ADR-003-repository-interface-refactoring.md)** | Repository Separation of Concerns | ✅ Implemented | 2025-10-04 | Medium |
| **[ADR-004](./ADR-004-harvest-module-consolidation.md)** | Harvest Module Consolidation | ✅ Implemented | 2025-10-05 | High |
| **[ADR-005](./ADR-005-service-layer-interfaces.md)** | Service Layer Interfaces & Type Safety | ✅ Implemented | 2025-10-11 | High |
| **[ADR-006](./ADR-006-api-layer-design.md)** | API Layer Design & FastAPI Integration | � Ready to Implement | 2025-10-26 | High |
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
**Status:** � **Ready to Implement** (Auth prerequisite complete)  
**Impact:** Exposes fermentation functionality via HTTP  
**Key Points:**
- 18 endpoints (10 fermentation + 8 sample)
- Pydantic v2 for request/response DTOs
- JWT authentication with multi-tenancy (✅ ADR-007 COMPLETE)
- OpenAPI documentation (Swagger UI)
- ~45 API tests, ~2100 lines of code
- Estimated: 3-4 days development
- **READY**: ADR-007 authentication infrastructure complete

### ADR-007: Authentication Module (Shared Infrastructure)
**Decision:** JWT-based auth in src/shared/auth/ with User entity, role-based authorization  
**Status:** ✅ **Implemented** (Nov 4, 2025)  
**Impact:** Unblocks all API layers, enforces multi-tenancy  
**Key Points:**
- User entity with winery_id (multi-tenancy)
- JWT tokens (15min access + 7 days refresh)
- 4 roles: Admin, Winemaker, Operator, Viewer
- FastAPI dependencies (get_current_user, require_role)
- **Test Coverage**: 186 tests passing (163 unit + 24 integration)
- PasswordService (bcrypt), JwtService (PyJWT), AuthService
- Migration completed: User moved from fermentation to shared/auth
- **UNBLOCKED**: API layers can now be implemented
- Password hashing (bcrypt/argon2)
- ~40 tests, ~1250 lines of code
- Estimated: 3 days (2 dev + 1 test)
- **PREREQUISITE**: Must be implemented before ADR-006

---

## 📊 Current Status (Oct 26, 2025)

**Implementation Complete:**
- ✅ Domain Layer (Entities, DTOs, Enums, Interfaces)
- ✅ Repository Layer (FermentationRepository + SampleRepository)
- ✅ Service Layer (FermentationService + SampleService + Validators)
- ✅ Total: 173 tests passing (100% for implemented layers)

**Next Phase (CRITICAL PATH):**
- 🔄 **ADR-007: Auth Module** (src/shared/auth/) - **IN PROGRESS**
- ⏳ ADR-006: API Layer (after auth is ready)

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
