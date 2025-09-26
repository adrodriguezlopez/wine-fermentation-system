# ADR-002: Arquitectura de Repositories (incl. Base Repository)

**Status:** Proposed  
**Date:** 2025-09-25  
**Authors:** Arquitectura de Fermentación (VintArch)

---

## Context
Ya existen interfaces `IFermentationRepository` y `ISampleRepository`.  
ADR-001 introdujo `winery_id` (multi-tenant) y blends multi-lot, que requieren consistencia transaccional.  
Necesitamos decidir: ¿habrá BaseRepository?, ¿cómo organizar transacciones y errores?, ¿cómo mantener boundaries del dominio?

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
10. **Return types** → Samples = entidades; Fermentations = dicts (MVP). Plan migrar a entidades.

---

## Implementation Notes (rápido acceso)
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


- **BaseRepository** → sesión, transacciones, error mapping, soft-delete.  
- **FermentationRepository** → ciclo de vida, optimistic lock.  
- **SampleRepository** → upsert, rangos, latest, soft-delete, bulk.  
- **ReadModels** → reporting.  

---

## Consequences
- ✅ Claridad de límites, reuso técnico sin contaminar dominio.  
- ✅ Transacciones correctas, testabilidad alta, multi-tenant listo.  
- ⚠️ Más clases y boilerplate.  
- ⚠️ Contrato inconsistente temporal (dict vs entidad).  
- ⚠️ Consultas complejas → ReadModels.  

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
- FermentationRepo dicts (MVP) → migrar a entidades.  
- Samples siempre ordenados, soft-delete aplicado.  
- HarvestLot = repo read-only.  

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
Proposed
