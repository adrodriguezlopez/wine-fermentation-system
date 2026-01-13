# Module Context: Winery Management

> **Parent Context**: See `/.ai-context/project-context.md` for system-level decisions  
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Module responsibility
**Winery identity and multi-tenancy root** - Represents winery organizations and provides the foundation for data isolation across the system.

**Position in system**: Root entity for multi-tenant architecture. All other modules reference winery for ownership and data scoping.

## Module interfaces
**Provides to**: All modules (winery_id for multi-tenant scoping)  
**Depends on**: None (root module, no dependencies)  
**Receives from**: User input (winery creation/management)

## Key functionality
- **Organization identity**: Represent winery as business entity
- **Multi-tenancy root**: Provide `winery_id` for data isolation
- **Ownership tracking**: Link all data (vineyards, fermentations, users) to winery

## Domain model

```
Winery (root)
  ↓ owns
  ├─ Vineyard (fruit_origin module)
  ├─ Fermentation (fermentation module)
  ├─ HarvestLot (fruit_origin module)
  └─ User (auth module, future)
```

## Entities

### Winery
**Purpose**: Winery organization entity  
**Key fields**: `code`, `name`, `location`, `notes`  
**Relationships**: 
- Has many Vineyards (fruit_origin)
- Has many Fermentations (fermentation)
- Has many HarvestLots (fruit_origin)
- Has many Users (auth module, future)

## Business rules
- **Unique code**: `code` must be globally unique
- **Required fields**: `code` and `name` are mandatory
- **Soft delete**: Cannot hard-delete winery with active data
- **Data isolation**: ALL queries across system must filter by `winery_id`

## Database tables
- `wineries` - Single table for winery entities

**Indexes**: `code` (unique)  
**Constraints**: Unique `code`, NOT NULL on `code` and `name`

## Implementation status

**Status:** ✅ **API LAYER COMPLETE** (ADR-016 ✅ + ADR-017 ✅)  
**Last Updated:** January 13, 2026  
**Total Tests:** 104 passing (44 unit + 35 integration + 25 API)

### Component status
- ✅ **Domain Layer**: Winery entity with SQLAlchemy mapping  
  See: [domain component-context.md](src/domain/.ai-context/component-context.md)

- ✅ **Repository Layer**: 22 unit tests passing (100%)  
  See: [repository_component component-context.md](src/repository_component/.ai-context/component-context.md)

- ✅ **Service Layer**: 22 unit tests + 17 integration tests (100%) - ADR-016 ✅  
  See: [service_component component-context.md](src/service_component/.ai-context/component-context.md)
  - WineryService with 9 methods
  - ValidationOrchestrator pattern
  - Cross-module deletion protection
  - Structured logging integration

- ✅ **API Layer**: COMPLETE (ADR-017 ✅) - 25 API tests passing (100%)  
  See: [api_component component-context.md](src/api_component/.ai-context/component-context.md)
  - Admin namespace: `/api/v1/admin/wineries`
  - 6 REST endpoints (CREATE, GET by ID, GET by code, LIST, UPDATE, DELETE)
  - Role-based authorization (ADMIN vs users)
  - 25 API tests (6 CREATE + 8 GET + 3 LIST + 5 UPDATE + 3 DELETE)
  - Pydantic v2 request/response DTOs
  - FastAPI dependency injection
  - Integration with shared auth module

### Next steps
- ⏭️ **Current**: Integrate with main application (register router)
- 📋 **Optional**: Seed script for bootstrap data
- 🔮 **Future**: Relationship endpoints (vineyards, fermentations)
- 🔮 **Future**: Advanced features (statistics, bulk operations, enhanced caching)

## Cross-module dependencies

**Outgoing** (winery depends on): None (root module)

**Incoming** (other modules depend on winery):
- `fruit_origin.Vineyard` - References via `winery_id`
- `fruit_origin.HarvestLot` - References via `winery_id`
- `fermentation.Fermentation` - References via `winery_id`
- `auth.User` - Will reference via `winery_id` (future)

## Multi-tenancy enforcement

**Critical**: `winery_id` must be in ALL queries that access user data.

**Security pattern**:
```python
# ✅ SAFE: Scoped by winery_id
stmt = select(Fermentation).where(
    Fermentation.id == fermentation_id,
    Fermentation.winery_id == winery_id  # ← Required
)

# ❌ DANGEROUS: No winery_id check
fermentation = await session.get(Fermentation, fermentation_id)
```

## Why separate module?

**Bounded context**: Winery represents "WHO owns the data" - distinct from:
- `fruit_origin` = "WHERE fruit came from"
- `fermentation` = "HOW wine is made"

**Architectural benefits**:
- Clear dependency direction: specific modules → winery (never reverse)
- Single source of truth for organization identity
- Can evolve independently (add legal info, branding, etc.)
- Multi-tenancy enforcement at root level

**Future extensions**:
- Legal information (tax ID, licenses)
- Personnel management (winemakers, roles)
- Configuration (default settings, units, thresholds)
- Branding (logo, colors)
- Multi-location support

## Module components
- ✅ **Domain Component**: Winery entity with SQLAlchemy mapping
- ✅ **Repository Component**: Data access for winery CRUD (ADR-009, ADR-016)
- ✅ **Service Component**: Business logic for winery management (ADR-016)
- 📋 **API Component**: Admin REST endpoints for winery operations (ADR-017 - proposed)

## Key architectural decisions
See [ADR-004](/.ai-context/adr/ADR-004-harvest-module-consolidation.md):
- **Separate module rationale**: Winery is distinct bounded context (organization identity)
- **Root entity**: Provides multi-tenant foundation for entire system
- **No dependencies**: Root module doesn't depend on other domain modules

## SQLAlchemy patterns used
- **Consistent imports**: `from src.shared.infra.orm.base_entity import BaseEntity`
- **extend_existing=True**: Test compatibility in `__table_args__`
- **Relationships**: Use fully-qualified paths when referencing from other modules

See: [ARCHITECTURAL_GUIDELINES.md](/.ai-context/ARCHITECTURAL_GUIDELINES.md) - Section "SQLAlchemy Import Best Practices"

## Implementation roadmap
1. ✅ Define repository interface in `src/domain/repositories/` (ADR-009)
2. ✅ Implement repository in `repository_component/` (ADR-009, ADR-016)
3. ✅ Create service layer for winery CRUD (ADR-016)
4. 📋 Add API endpoints for winery management (ADR-017 - in progress)
5. 📋 Add seed script for bootstrap (ADR-017 - Phase 3)
6. 🔮 Future: Advanced features (statistics, audit trail, bulk operations)
