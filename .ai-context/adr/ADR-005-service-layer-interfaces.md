# ADR-005: Service Layer Interface Refactoring & Type Safety

**Status:** ✅ Implemented (Oct 25, 2025)  
**Date:** 2025-10-11  
**Deciders:** Development Team  
**Related ADRs:** ADR-002 (Repository Architecture), ADR-003 (Repository Separation of Concerns)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño

---

## Context

Las interfaces de servicio (`IFermentationService` y `ISampleService`) tenían problemas fundamentales:
1. Sin type safety (usaban `Dict[str, Any]`)
2. Retornaban primitivos en vez de entidades
3. Mezclaban responsabilidades (FermentationService manejaba samples)
4. Inconsistentes con repository layer
5. Sin enforcement de multi-tenancy
6. Operaciones incompletas
7. Sin validación dry-run

---

## Decision

### 1. Refactorización completa de interfaces

**IFermentationService (7 métodos):**
- `create_fermentation(winery_id, user_id, data: FermentationCreate) -> Fermentation`
- `get_fermentation(fermentation_id, winery_id) -> Optional[Fermentation]`
- `get_fermentations_by_winery(winery_id, status?, include_completed?) -> List[Fermentation]`
- `update_status(fermentation_id, winery_id, new_status, user_id) -> bool`
- `complete_fermentation(fermentation_id, winery_id, user_id, final_sugar_brix, final_mass_kg) -> bool`
- `soft_delete(fermentation_id, winery_id, user_id) -> bool`
- `validate_creation_data(data: FermentationCreate) -> ValidationResult`

**ISampleService (6 métodos):**
- `add_sample(fermentation_id, winery_id, user_id, data: SampleCreate) -> BaseSample`
- `get_sample(sample_id, fermentation_id, winery_id) -> Optional[BaseSample]`
- `get_samples_by_fermentation(fermentation_id, winery_id) -> List[BaseSample]`
- `get_latest_sample(fermentation_id, winery_id, sample_type?) -> Optional[BaseSample]`
- `get_samples_in_timerange(fermentation_id, winery_id, start, end) -> List[BaseSample]`
- `validate_sample_data(fermentation_id, data: SampleCreate) -> ValidationResult`

### 2. Type Safety
- DTOs para input (`FermentationCreate`, `SampleCreate`)
- Entidades para output (`Fermentation`, `BaseSample`)
- NO más `Dict[str, Any]`

### 3. Multi-tenancy enforcement
- `winery_id` requerido en todas las operaciones
- `user_id` para audit trail

### 4. Validator extraction (SRP)
- `IFermentationValidator` interface creada
- Validación separada de orquestación

---

## Implementation Notes

```
src/modules/fermentation/src/service_component/
├── interfaces/
│   ├── fermentation_service_interface.py      # 7 métodos
│   ├── sample_service_interface.py            # 6 métodos
│   └── fermentation_validator_interface.py    # 3 métodos
├── services/
│   ├── fermentation_service.py                # 410 lines
│   └── sample_service.py                      # 460 lines
├── validators/
│   └── fermentation_validator.py              # 175 lines
└── errors.py                                   # 57 lines
```

**Responsabilidades:**
- **Services**: Orquestación, multi-tenancy, audit trail
- **Validators**: Reglas de negocio, state machine
- **Errors**: Excepciones semánticas (NotFoundError, ValidationError, etc.)

---

## Consequences

### ✅ Benefits
- Type safety completo (IDE autocomplete, compile-time checks)
- Clean Architecture compliance
- SOLID principles enforced
- Testabilidad mejorada (mocking fácil)
- Consistencia cross-layer
- Multi-tenancy enforced

### ⚠️ Trade-offs
- Breaking changes (interfaces incompatibles con versión anterior)
- Más parámetros en métodos (+winery_id, +user_id)
- Firmas más verbosas

### ❌ Limitations
- Requiere actualizar todos los consumers
- No backward compatible

---

## Quick Reference

**Service Layer Pattern:**
```python
# Input: DTOs (type-safe)
# Output: Entities (rich domain objects)
# Dependencies: Injected via constructor (DI)
# Errors: Semantic exceptions (NotFoundError, ValidationError)
```

**Multi-tenancy:**
- All operations scoped by `winery_id`
- Security by obscurity (NotFoundError for unauthorized access)

**Validation:**
- Creation/Update: Via `IFermentationValidator`
- Dry-run: `validate_*_data()` methods
- No side effects in validation

**Audit Trail:**
- `user_id` tracked in create/update/delete operations
- Soft-delete support via `deleted_at` timestamp

---

## Implementation Status

**✅ Completed (Oct 25, 2025):**
- FermentationService: 7/7 methods (33 tests, 100% passing)
- SampleService: 6/6 methods (27 tests, 100% passing)
- FermentationValidator: 3/3 methods (12 tests, 100% passing)
- **Total: 72/72 tests passing**

**Production Ready:** Both services ready for API layer integration

---

## Error Catalog

```python
ServiceError (base)
├── ValidationError      # Business rule violations
├── NotFoundError       # Resource not found / unauthorized
├── DuplicateError      # Resource already exists
└── BusinessRuleViolation  # Generic business rule
```

**Mapping to HTTP:**
- `ValidationError` → 400 Bad Request
- `NotFoundError` → 404 Not Found
- `DuplicateError` → 409 Conflict
- `RepositoryError` → 500 Internal Server Error

---

## Status

✅ **Accepted** - Fully implemented, production ready
