# ADR-002: Arquitectura de Repositories (incl. Base Repository)

**Status:** Proposed  
**Date:** 2025-09-25  
**Authors:** Arquitectura de Fermentación (VintArch)

> **📋 Context Files:** Para revisión completa, leer también:
> - [Implementation Summary](./ADR-002-repositories-architecture-implementation-summary.md) - Estado actual
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> - [Project Structure Map](../PROJECT_STRUCTURE_MAP.md) - Navegación del proyecto

---

## Context
Ya existen interfaces `IFermentationRepository` y `ISampleRepository`.  
ADR-001 introdujo `winery_id` (multi-tenant) y blends multi-lot, que requieren consistencia transaccional.  
Necesitamos decidir: ¿habrá BaseRepository?, ¿cómo organizar transacciones y errores?, ¿cómo mantener boundaries del dominio?  
**Arquitectura base debe seguir principios SOLID y Clean Architecture** para asegurar mantenibilidad y testabilidad.

---

## Decision
1. **Ports & Adapters** → cada agregado define su interfaz; no generic repo de dominio.  
2. **BaseRepository (infra-helper)** → solo helpers técnicos (session, errores, soft-delete). No invariantes.  
3. **Unit of Work (UoW)** → async context manager para blends y bulk.  
4. **Scoping multi-tenant** → todas queries con winery_id.  
5. **Optimistic locking** → campo `version` en Fermentation.  
6. **Query patterns** → SampleRepo = time-series; FermentationRepo = ciclo de vida; reporting via ReadModels.  
7. **Error Mapping** → centralizado en BaseRepository, errores de DB → catálogo repositorio.  
8. **Soft-delete** → samples con is_deleted; siempre filtrar.  
9. **Boundaries fruit_origin** → HarvestLot vía repo read-only.  
10. **Return types** → Both Samples and Fermentations return entities (domain objects).  
11. **Interface-Based Design** → Dependency Inversion via protocols (IDatabaseConfig, ISessionManager, IBaseRepository).  
12. **SOLID Compliance** → SRP (single responsibility), OCP (open/closed), LSP (Liskov substitution), ISP (interface segregation), DIP (dependency inversion).

---

## Implementation Notes (rápido acceso)
```
src/modules/fermentation/
domain/repositories/
IFermentationRepository.py
ISampleRepository.py
infrastructure/db/
base_repository.py
fermentation_repository.py
sample_repository.py
unit_of_work.py
infrastructure/readmodels/
fermentation_queries.py
```

**SOLID Principles Applied:**
- **S**RP: BaseRepository (technical helpers), FermentationRepository (domain logic), SampleRepository (time-series)
- **O**CP: Extensible via interfaces without modifying existing implementations  
- **L**SP: All repository implementations substitutable via their interfaces
- **I**SP: Specific interfaces (IFermentationRepository ≠ ISampleRepository ≠ IBaseRepository)
- **D**IP: Dependencies on abstractions (ISessionManager, IDatabaseConfig) not concretions

**Clean Architecture Layers:**
- **Domain Layer**: Repository interfaces (IFermentationRepository, ISampleRepository)
- **Infrastructure Layer**: Concrete implementations + database specifics  
- **Shared Infrastructure**: Session management, error mapping, database config

- **BaseRepository** → sesión, transacciones, error mapping, soft-delete.  
- **FermentationRepository** → ciclo de vida, optimistic lock, returns Fermentation entities.  
- **SampleRepository** → upsert, rangos, latest, soft-delete, bulk, returns BaseSample entities.  
- **ReadModels** → reporting, returns DTOs/dicts for optimized queries.  

---

## Consequences
- ✅ Claridad de límites, reuso técnico sin contaminar dominio.  
- ✅ Transacciones correctas, testabilidad alta, multi-tenant listo.  
- ✅ Consistent entity return types across all repositories.  
- ✅ SOLID compliance ensures maintainability and extensibility.
- ✅ Clean Architecture enables independent testing and deployment.
- ✅ Dependency Inversion facilitates mocking and unit testing.
- ⚠️ Más clases y boilerplate.  
- ⚠️ Consultas complejas → ReadModels.  
- ⚠️ Interface overhead in simple scenarios.  

---

## TDD Plan
- **BaseRepository error mapping** → IntegrityError correcto.  
- **SampleRepository.get_samples_in_timerange** → orden ASC, excluye soft-delete.  
- **FermentationRepository.update_status** → optimistic lock.  
- **UoW blend** → rollback atómico.  

---

## Quick Reference (para devs apurados)
- No generic repo → cada agregado su interfaz.  
- Sí BaseRepository → helpers técnicos.  
- UoW async → blends y bulk.  
- winery_id obligatorio en queries.  
- Both repositories return domain entities consistently.  
- Samples siempre ordenados, soft-delete aplicado.  
- HarvestLot = repo read-only.  
- **SOLID + Clean Architecture** → interfaces mandatory, dependency inversion enforced.
- **TDD approach** → tests first, implementation second.  

---

## API Examples
```python
# UoW usage for blends
async with unit_of_work() as uow:
    fermentation = await uow.fermentation_repo.get_by_id(123, winery_id=1)
    for lot_source in blend_data:
        await uow.fermentation_repo.add_lot_source(fermentation, lot_source)
    await uow.commit()

# Optimistic lock failure
try:
    await uow.fermentation_repo.update(fermentation, expected_version=5)
except ConcurrentModificationError as e:
    handle_conflict(e)
```

## Error Catalog
- IntegrityError (SQLSTATE 23505) → DuplicateEntityError
- ForeignKeyViolation (23503) → ReferentialIntegrityError
- SerializationFailure (40001), DeadlockDetected (40P01) → RetryableConcurrencyError
- NotFound (no rows, scoped by winery_id) → EntityNotFoundError
- OptimisticLockError → ConcurrentModificationError (with expected vs actual version)

## Acceptance Criteria
- [ ] All queries scoped by winery_id
- [ ] Soft-deleted samples never returned
- [ ] UoW rollback leaves DB unchanged
- [ ] Optimistic lock prevents concurrent updates
- [ ] SQLSTATE error mapping covered by tests
- [ ] Repos do not manage transactions when UoW is active
- [ ] ReadModels return DTOs, not Entities
- [ ] Batch operations idempotent under retry

## Status
In Progress

---

## Updates & Related ADRs

**ADR-003 (2025-10-04):** Repository Interface Refactoring
- Fixed circular import issues in entities
- Synchronized repository interface with actual SQLAlchemy model
- Improved TYPE_CHECKING usage

**ADR-004 (2025-10-05):** Harvest Module Consolidation & SQLAlchemy Registry Fix
- **SQLAlchemy Patterns:** Fully-qualified paths in relationships required to avoid registry conflicts
- **Import Consistency:** All entities must import BaseEntity from `src.shared.infra.orm.base_entity`
- **Test Fixtures:** Use `flush()` instead of `commit()` to maintain transaction context
- **Single-Table Inheritance:** Use `viewonly=True` for unidirectional relationships
- See ARCHITECTURAL_GUIDELINES.md for complete SQLAlchemy best practices

**Cross-References:**
- `.ai-context/ARCHITECTURAL_GUIDELINES.md` - Section: "🗄️ SQLAlchemy Import Best Practices"
- `.ai-context/PROJECT_STRUCTURE_MAP.md` - Current module structure with 7 modules
- `.ai-context/fermentation/module-context.md` - Fermentation bounded context details
- `.ai-context/fruit_origin/module-context.md` - HarvestLot now in separate module
