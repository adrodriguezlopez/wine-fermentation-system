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

**Status:** ✅ **Domain & Repository Layer Complete** | 🎯 **Tests Passing (22 unit + 18 integration)**  
**Last Updated:** December 15, 2025  
**Reference:** ADR-009 (Missing Repositories), ADR-012 (Unit Testing Phase 3)

### Completed
- ✅ Entity model with SQLAlchemy mapping
  - Winery: 4 fields (code, name, location, notes)
  - Unique constraints: code (globally unique)
  - Indexed: code
- ✅ Database table created (wineries)
- ✅ **Repository Layer (22 unit + 18 integration tests)**
  - WineryRepository: Complete CRUD operations ✅
  - 22 unit tests (Phase 3 migrated to ADR-012) ✅
  - 18 integration tests ✅
  - Multi-tenant ready (no winery_id filtering needed - root entity)
  - Error handling (DuplicateNameError, RepositoryError)
  - Soft-delete support
- ✅ **ADR-012 Impact**: 1 repository test file migrated (22 tests using shared infrastructure)

### Pending
- ⏭️ Service layer (winery CRUD operations)
- ⏭️ API endpoints

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
Currently only **Domain** component (entity). Future:
- **Repository Component**: Data access for winery CRUD
- **Service Component**: Business logic for winery management
- **API Component**: Endpoints for winery operations

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

## Next steps
1. Define repository interface in `src/domain/repositories/`
2. Implement repository in `repository_component/`
3. Create service layer for winery CRUD
4. Add API endpoints for winery management
5. Add access control (users can only access their winery's data)
