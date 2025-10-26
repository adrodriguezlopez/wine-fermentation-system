# ADR-003: Repository Separation of Concerns

**Status:** ✅ Implemented  
**Date:** 2025-10-04  
**Deciders:** Development Team  
**Related ADRs:** ADR-002 (Repository Architecture)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios SOLID

---

## Context

FermentationRepository violaba el Single Responsibility Principle al manejar tanto fermentations como samples:

**Problemas identificados:**
1. **Responsabilidades mezcladas**: `add_sample()` y `get_latest_sample()` en FermentationRepository
2. **Imports circulares**: Dependencias entre entidades mal estructuradas
3. **Código duplicado**: Clases redefinidas en repositorios en vez de importar
4. **Inconsistencia**: ISampleRepository duplicaba algunos métodos

---

## Decision

### 1. Separación estricta de repositorios

**IFermentationRepository (5 métodos):**
- `create()` - Crear fermentación
- `get_by_id()` - Obtener por ID
- `update_status()` - Actualizar estado
- `get_by_status()` - Filtrar por estado
- `get_by_winery()` - Listar por bodega
- ❌ **ELIMINADO**: `add_sample()`, `get_latest_sample()`

**ISampleRepository (11 métodos):**
- `create()` / `upsert_sample()` - Crear/actualizar sample
- `get_sample_by_id()` - Obtener por ID
- `get_samples_by_fermentation_id()` - Listar por fermentación
- `get_latest_sample()` - Obtener más reciente
- `get_latest_sample_by_type()` - Filtrar por tipo
- `get_samples_in_timerange()` - Rango de tiempo
- `get_fermentation_start_date()` - Helper para validación
- `check_duplicate_timestamp()` - Validación duplicados
- `soft_delete_sample()` - Borrado lógico
- `bulk_upsert_samples()` - Operaciones masivas

### 2. Fix de imports circulares
- Imports relativos dentro de paquetes (`from .base_sample`)
- TYPE_CHECKING con paths absolutos para type hints
- `extend_existing=True` en tablas SQLAlchemy

### 3. Eliminación de código duplicado
- Importar desde ubicaciones canónicas
- Single source of truth para cada clase

---

## Implementation Notes

```
src/modules/fermentation/src/repository_component/
├── interfaces/
│   ├── fermentation_repository_interface.py   # 5 métodos
│   └── sample_repository_interface.py         # 11 métodos
└── repositories/
    ├── fermentation_repository.py             # Implementación completa
    └── sample_repository.py                   # Implementación completa
```

**Cambios aplicados:**
- Eliminados ~280 líneas de FermentationRepository (samples logic)
- Eliminados 5 tests de samples en FermentationRepository
- Agregados 11 métodos + 12 tests en SampleRepository
- Total: 102 tests passing (antes: 95)

---

## Consequences

### ✅ Benefits
- SRP enforcement: Un repositorio = un aggregate root
- Testabilidad mejorada: Tests enfocados
- Mantenibilidad: Cambios en samples no afectan FermentationRepository
- Dependencias explícitas en services

### ⚠️ Trade-offs
- Services deben inyectar ambos repositorios
- Breaking changes en código existente

### ❌ Limitations
- Requiere actualizar service layer para inyectar SampleRepository

---

## Service Layer Usage

```python
# Service con dependencias explícitas
class FermentationService:
    def __init__(
        self, 
        fermentation_repo: IFermentationRepository,
        sample_repo: ISampleRepository
    ):
        self._fermentation_repo = fermentation_repo
        self._sample_repo = sample_repo
    
    async def add_measurement(self, fermentation_id, data):
        # Delega a SampleRepository
        sample = BaseSample(...)
        return await self._sample_repo.upsert_sample(sample)
```

---

## Quick Reference

**Principio:** One repository = One aggregate root

**FermentationRepository:**
- ✅ Fermentation lifecycle ONLY
- ❌ NO sample operations

**SampleRepository:**
- ✅ Sample CRUD operations
- ✅ Queries and validations
- ✅ Bulk operations

**Import fixes:**
- Relative imports: `from .base_sample`
- TYPE_CHECKING: Full absolute paths
- No circular dependencies

---

## Status

✅ **Accepted** - Fully implemented, 102/102 tests passing
