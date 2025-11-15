# Component Context: Domain Component (Winery Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions  
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Defines the core business model for winery organization identity. Centralizes the root entity for multi-tenancy and provides the foundation for data isolation across the entire system.

**Position in module**: Foundation layer - simplest domain component (single entity). All other modules reference winery for ownership and scoping. Domain does not depend on any other component.

## Architecture pattern
- **Domain-Driven Design (DDD)**: Single aggregate root (Winery)
- **Dependency Inversion Principle**: All dependencies point inward to domain
- **Multi-tenancy root**: Winery is the organizational boundary

## Arquitectura específica del componente
- **Entities**: Winery (in `entities/`)
- **Repository Interfaces**: (pending) IWineryRepository (future in `repositories/`)
- **No infrastructure logic**: Only contracts and pure domain model

## Domain model

```
Winery (Root Entity)
  ├─ id: int (PK)
  ├─ code: str (unique)
  ├─ name: str
  ├─ location: str (optional)
  ├─ notes: str (optional)
  ├─ created_at: datetime
  ├─ updated_at: datetime
  ├─ deleted_at: datetime (soft delete)
  └─ is_deleted: bool
```

**Relationships** (conceptual - implemented in other modules):
- Has many Vineyards (fruit_origin module)
- Has many Fermentations (fermentation module)
- Has many HarvestLots (fruit_origin module)
- Has many Users (auth module, future)

## Business rules enforced

### Winery
- **Global uniqueness**: `code` must be unique across all wineries
- **Required fields**: `code` and `name` are mandatory
- **Code format**: Uppercase alphanumeric with hyphens (e.g., "BODEGA-001")
- **Soft delete only**: Cannot hard-delete winery with active data
- **Multi-tenant isolation**: All child data must be filtered by `winery_id`

### Security rules
- **Data isolation**: Queries across system MUST include `winery_id` filter
- **Cross-tenant prevention**: No user can access data from other wineries
- **Ownership validation**: All entities that reference `winery_id` must validate ownership

## Component interfaces

### Future Repository Interface (Pending Implementation)

**IWineryRepository** (future):
- `create(winery: Winery) → Winery`
- `get_by_id(id: int) → Winery`
- `get_by_code(code: str) → Winery`
- `get_all(include_deleted: bool = False) → List[Winery]`
- `update(winery: Winery) → Winery`
- `soft_delete(id: int) → bool`
- `restore(id: int) → bool`
- `can_delete(id: int) → bool` (check if has active data)

## Connection with other components

**Future components** (pending):
- **Repository Component**: Will implement IWineryRepository
- **Service Component**: Will use Winery entity for CRUD operations
- **API Component**: Will expose winery management endpoints

**Cross-module dependencies**:
- **Used by ALL modules**: Every module references `winery_id` for multi-tenancy
  - `fruit_origin.Vineyard.winery_id` → `Winery.id`
  - `fruit_origin.HarvestLot.winery_id` → `Winery.id`
  - `fermentation.Fermentation.winery_id` → `Winery.id`
  - `auth.User.winery_id` → `Winery.id` (future)

## Implementation status

**Status:** ✅ **Entity Complete** - Repository interface pending  
**Last Updated:** 2025-10-05

### Completed
- ✅ Winery entity model
- ✅ SQLAlchemy mapping
- ✅ Business rules in entity constraints
- ✅ Integration test fixture (test_winery)

### Pending
- ⏭️ Repository interface definition (IWineryRepository)
- ⏭️ Validation logic (code format, uniqueness)
- ⏭️ Cascade delete prevention logic

## Key implementation considerations

### Multi-tenancy enforcement

**CRITICAL**: This is the MOST important business rule in the entire system.

```python
# ✅ CORRECT: All queries MUST scope by winery_id
stmt = select(Fermentation).where(
    Fermentation.id == fermentation_id,
    Fermentation.winery_id == winery_id  # ← REQUIRED
)

# ❌ DANGEROUS: No winery_id check = security vulnerability
fermentation = await session.get(Fermentation, fermentation_id)
```

**Why this matters**:
- Prevents data leakage between wineries
- Regulatory compliance (data privacy)
- Business isolation (proprietary patterns remain private)

### SQLAlchemy Patterns
- **Consistent imports**: `from src.shared.infra.orm.base_entity import BaseEntity`
- **extend_existing=True**: For test compatibility
- **Unique constraint**: `code` must be globally unique

### Soft delete strategy
- **Never hard-delete**: Maintain audit trail
- **Cascade consideration**: Check for active vineyards, fermentations before soft-delete
- **Restoration support**: Allow winery reactivation if needed

## Why Winery is a separate module?

**Bounded Context**: Winery represents "WHO owns the data" - distinct from:
- `fruit_origin` = "WHERE fruit came from"
- `fermentation` = "HOW wine is made"

**Architectural benefits**:
1. **Clear dependency direction**: Specific modules → winery (never reverse)
2. **Single source of truth**: One place for organization identity
3. **Independent evolution**: Can add legal info, branding, etc. without affecting other modules
4. **Root-level enforcement**: Multi-tenancy at the foundation

## Future enhancements

### Organizational features
1. **Legal information**: Tax ID, business licenses, regulatory compliance
2. **Contact information**: Address, phone, email, website
3. **Personnel**: Winemakers, roles, permissions
4. **Branding**: Logo, color scheme, marketing materials

### Configuration
1. **Default settings**: Preferred units (metric/imperial)
2. **QA thresholds**: Alert levels for pH, temperature, etc.
3. **Fermentation protocols**: Standard procedures per winery

### Advanced features
1. **Multi-location support**: Wineries with multiple facilities
2. **Production capacity**: Track equipment, tank inventory
3. **Subscription/billing**: If system becomes SaaS
4. **API keys**: For integration with external systems

## References
- **ADR-004**: Harvest Module Consolidation & SQLAlchemy Registry Fix
- **Module Context**: `../../.ai-context/module-context.md`
- **ARCHITECTURAL_GUIDELINES**: `/.ai-context/ARCHITECTURAL_GUIDELINES.md` - Multi-tenancy patterns
