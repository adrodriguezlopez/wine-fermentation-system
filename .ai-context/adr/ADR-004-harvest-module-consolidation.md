# ADR-004: Harvest Module Consolidation & SQLAlchemy Registry Fix

**Status:** ✅ Implemented  
**Date:** 2025-10-05  
**Deciders:** Development Team  
**Related ADRs:** ADR-001 (Folder Structure), ADR-003 (Repository Refactoring)

---

## Context

Durante la implementación de los tests de integración del módulo `fermentation`, se descubrieron dos problemas arquitectónicos críticos:

### Problema 1: Duplicación del módulo HarvestLot
- **Síntoma:** Existían dos módulos separados con la misma entidad `HarvestLot`:
  - `src/modules/harvest/` (5 campos básicos)
  - `src/modules/fruit_origin/` (19 campos completos con trazabilidad)
- **Impacto:** Confusión arquitectónica, duplicación de código, decisiones inconsistentes sobre dónde implementar funcionalidades

### Problema 2: SQLAlchemy Registry Conflicts
- **Síntoma:** Error "Multiple classes found for path 'X'" en tests de integración
- **Causa raíz:** Combinación de varios factores:
  1. Uso de paths cortos en relationships (`"BaseSample"` en lugar de paths completos)
  2. Single-table inheritance con relationships bidireccionales
  3. Inconsistencias en imports (algunos con `from .x import`, otros sin)

---

## Decision

### 1. Consolidación de Módulos (Harvest → fruit_origin)

**Decisión:** Eliminar `src/modules/harvest/` y usar exclusivamente `src/modules/fruit_origin/`

**Razones:**
- **Bounded Context correcto:** `fruit_origin` representa el contexto completo del "origen del fruto":
  - `Vineyard` (viñedo)
  - `VineyardBlock` (parcela del viñedo)  
  - `HarvestLot` (lote cosechado de una parcela)
- **Trazabilidad completa:** `fruit_origin/HarvestLot` tiene 19 campos vs 5 campos de `harvest/HarvestLot`
- **Relaciones correctas:** `HarvestLot` → `VineyardBlock` → `Vineyard` → `Winery`
- **Constraints adecuados:** `UniqueConstraint('code', 'winery_id')` para multi-tenancy

### 2. SQLAlchemy Registry Fix

**Decisión:** Implementar 3 estrategias para evitar conflictos de registro:

#### 2.1 Fully-Qualified Paths en Relationships
```python
# ❌ ANTES (ambiguo)
samples: Mapped[List["BaseSample"]] = relationship(
    "BaseSample",
    back_populates="fermentation"
)

# ✅ DESPUÉS (explícito)
samples: Mapped[List["BaseSample"]] = relationship(
    "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
    back_populates="fermentation"
)
```

#### 2.2 Unidirectional Relationships para Herencia Polimórfica
```python
# En BaseSample (single-table inheritance)
fermentation: Mapped["Fermentation"] = relationship(
    "src.modules.fermentation.src.domain.entities.fermentation.Fermentation",
    viewonly=True  # ← Unidireccional
)

# En Fermentation (sin back_populates)
samples: Mapped[List["BaseSample"]] = relationship(
    "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
    cascade="all, delete-orphan"
    # NO back_populates para evitar conflictos con herencia
)
```

#### 2.3 Transacciones en Fixtures (flush vs commit)
```python
# ❌ ANTES (cierra transacciones)
await db_session.commit()
await db_session.refresh(obj)

# ✅ DESPUÉS (mantiene transacción abierta)
await db_session.flush()  # Asigna IDs sin commit
# El context manager hace rollback automático
```

---

## Consequences

### Positivas ✅

1. **Arquitectura limpia:**
   - Un solo bounded context para origen del fruto
   - Eliminada duplicación de código
   - Relaciones entre entidades claras y correctas

2. **Tests estables:**
   - 102/102 unit tests passing
   - 1/1 integration test passing
   - No más "Multiple classes found" errors

3. **Trazabilidad completa:**
   - HarvestLot con 19 campos (vs 5 anteriores)
   - Datos de calidad: `brix_at_harvest`, `brix_method`
   - Detalles de cosecha: `pick_method`, `pick_start_time`, `bins_count`
   - Datos técnicos: `clone`, `rootstock`, `field_temp_c`

4. **Base de datos actualizada:**
   ```sql
   wineries
   vineyards              ← NUEVO
   vineyard_blocks        ← NUEVO
   harvest_lots           ← ACTUALIZADO (19 campos)
   fermentations
   fermentation_lot_sources
   samples
   users
   fermentation_notes
   ```

### Negativas ⚠️

1. **Relationships verbosos:** Los fully-qualified paths son largos
   - **Mitigación:** Beneficio de claridad supera la verbosidad
   - **Alternativa considerada:** Aliases (descartada por opacar origen)

2. **Relationships unidireccionales:** No se puede navegar `sample.fermentation` en algunos casos
   - **Mitigación:** Usar queries explícitas cuando se necesite navegación inversa
   - **Impacto:** Bajo - la mayoría de navegaciones van de Fermentation → Samples

---

## Implementation Details

### Archivos Modificados (8):

1. **Imports actualizados:**
   - `tests/integration/conftest.py`
   - `recreate_test_tables.py`
   - `debug_sqlalchemy_registry.py`
   - `debug_registry_simple.py`
   - `debug_conftest_simulation.py`

2. **Entities corregidas (fruit_origin):**
   - `harvest_lot.py` - Fixed import + `extend_existing`
   - `vineyard.py` - Fixed import + `extend_existing`
   - `vineyard_block.py` - Fixed import + `extend_existing`

3. **Entities corregidas (fermentation):**
   - `user.py` - Fully-qualified paths + typo fix (`usernmame` → `username`)
   - `fermentation.py` - Fully-qualified paths
   - `base_sample.py` - Fully-qualified paths + viewonly
   - `fermentation_note.py` - Fully-qualified paths + Mapped types

4. **Repository actualizado:**
   - `sample_repository.py` - Added `recorded_by_user_id` en creación de samples

### Nuevos Fixtures (3):

```python
@pytest_asyncio.fixture
async def test_vineyard(db_session, test_winery): ...

@pytest_asyncio.fixture
async def test_vineyard_block(db_session, test_vineyard): ...

@pytest_asyncio.fixture
async def test_harvest_lot(db_session, test_winery, test_vineyard_block): ...
```

### Módulo Eliminado:

```
❌ src/modules/harvest/  (DELETED)
```

---

## Lessons Learned

### SQLAlchemy Best Practices

1. **Fully-Qualified Paths:** Siempre usar rutas completas en `relationship()` para evitar ambigüedad
2. **Single-Table Inheritance:** Con polimorfismo, considerar relationships unidireccionales
3. **Transaction Management:** En tests, usar `flush()` en lugar de `commit()` para mantener contexto transaccional
4. **`extend_existing=True`:** Necesario en `__table_args__` para permitir re-registro en tests

### Architectural Patterns

1. **Bounded Contexts:** Agrupar entidades relacionadas en un solo módulo conceptual
2. **Dependency Direction:** Cross-module dependencies deben ir de específico → general (fermentation → fruit_origin, NO al revés)
3. **Unique Constraints:** Multi-tenancy requiere constraints compuestos: `(code, winery_id)`

---

## Related Changes

- **ADR-001:** Updated folder structure (eliminated harvest/, consolidated fruit_origin/)
- **ADR-003:** Builds on import best practices from circular import resolution
- **ARCHITECTURAL_GUIDELINES.md:** Added section on SQLAlchemy imports
- **PROJECT_STRUCTURE_MAP.md:** Updated module structure

---

## Verification

### Tests Passing:
```bash
✅ poetry run pytest tests/unit/ -v      # 102/102 passing
✅ poetry run pytest tests/integration/ -v  # 1/1 passing
```

### Database Tables:
```bash
✅ poetry run python recreate_test_tables.py
Created tables: ['users', 'fermentations', 'fermentation_notes', 
                'fermentation_lot_sources', 'samples', 'wineries', 
                'vineyards', 'vineyard_blocks', 'harvest_lots']
```

### No Broken References:
```bash
✅ grep -r "from.*modules\.harvest" src/  # No matches
```

---

**Decision Date:** 2025-10-05  
**Implementation Date:** 2025-10-05  
**Status:** ✅ Implemented and Verified
