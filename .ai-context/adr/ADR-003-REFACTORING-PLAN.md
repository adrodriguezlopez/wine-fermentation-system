# ADR-003 Addendum - Refactoring Execution Plan

**Fecha:** 2025-10-04  
**Objetivo:** Separación completa de responsabilidades entre FermentationRepository y SampleRepository

---

## 📋 Estado Actual

### IFermentationRepository
**Métodos implementados:** 7
- ✅ `create()` - Crear fermentación
- ✅ `get_by_id()` - Obtener por ID
- ✅ `update_status()` - Actualizar estado
- ❌ `add_sample()` - **A ELIMINAR** (responsabilidad de samples)
- ❌ `get_latest_sample()` - **A ELIMINAR** (responsabilidad de samples)
- ✅ `get_by_status()` - Filtrar por estado
- ✅ `get_by_winery()` - Obtener por bodega

**Tests:** 13 tests (5 serán eliminados)

### ISampleRepository
**Métodos definidos:** 10
**Implementación:** ❌ NO EXISTE

---

## 🎯 Plan de Refactorización

### Fase 1: Actualizar Interfaces ✅

**1.1. IFermentationRepository**
- [x] Eliminar `add_sample()` de la interfaz
- [x] Eliminar `get_latest_sample()` de la interfaz
- [x] Agregar nota sobre ISampleRepository
- [x] Actualizar docstrings

**1.2. test_fermentation_repository_interface.py**
- [ ] Actualizar `required_methods` (eliminar add_sample, get_latest_sample)
- [ ] Agregar comentario explicativo

**Resultado esperado:** 7 métodos en IFermentationRepository (SOLO fermentation lifecycle)

---

### Fase 2: Refactorizar FermentationRepository Implementation

**2.1. fermentation_repository.py**
- [ ] Eliminar método `add_sample()`
- [ ] Eliminar método `get_latest_sample()`
- [ ] Actualizar docstring de clase
- [ ] Verificar no hay referencias a sample logic

**2.2. test_fermentation_repository.py**
Tests a ELIMINAR:
- [ ] `test_add_sample_raises_error_when_fermentation_not_found`
- [ ] `test_add_sample_creates_sugar_sample_when_glucose_provided`
- [ ] `test_get_latest_sample_returns_none_when_no_samples`
- [ ] `test_get_latest_sample_returns_most_recent_sample`
- [ ] `test_get_latest_sample_raises_error_when_fermentation_not_found`

Tests a MANTENER (8):
- [x] `test_repository_inherits_from_base_repository`
- [x] `test_create_returns_fermentation_entity`
- [x] `test_get_by_id_returns_none_when_not_found`
- [x] `test_get_by_id_returns_fermentation_when_found`
- [x] `test_update_status_returns_false_when_not_found`
- [x] `test_update_status_returns_true_when_successful`
- [x] `test_get_by_status_returns_list_of_fermentations`
- [x] `test_get_by_winery_returns_all_fermentations_for_winery`

**Resultado esperado:** 8 tests pasando (SOLO operaciones de fermentation)

---

### Fase 3: Implementar SampleRepository (TDD)

**3.1. Crear SampleRepository Implementation**

Archivo: `src/repository_component/repositories/sample_repository.py`

```python
"""
Sample Repository Implementation.

Concrete implementation of ISampleRepository that extends BaseRepository
and provides database operations for sample data management.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError

class SampleRepository(BaseRepository, ISampleRepository):
    """
    Repository for sample data operations.
    
    Implements ISampleRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and soft delete support.
    """
    
    # Implementar los 10 métodos de ISampleRepository
    pass
```

**3.2. Crear Test Suite**

Archivo: `tests/unit/repository_component/test_sample_repository.py`

Estructura de tests:
- `test_repository_inherits_from_base_repository`
- `test_upsert_sample_creates_new_sample`
- `test_upsert_sample_updates_existing_sample`
- `test_get_sample_by_id_returns_sample`
- `test_get_sample_by_id_raises_error_when_not_found`
- `test_get_samples_by_fermentation_id_returns_all_samples`
- `test_get_samples_in_timerange_filters_correctly`
- `test_get_latest_sample_returns_most_recent`
- `test_get_latest_sample_by_type_filters_correctly`
- `test_check_duplicate_timestamp_detects_duplicates`
- `test_soft_delete_sample_marks_as_deleted`
- `test_bulk_upsert_samples_handles_multiple_samples`

**Total tests esperados:** ~15-20 tests

---

### Fase 4: Validación

**4.1. Ejecutar Test Suite Completo**
```bash
cd src/modules/fermentation
python -m pytest tests/unit/ -v
```

**Resultado esperado:**
- FermentationRepository: 8 tests ✅
- SampleRepository: ~15-20 tests ✅
- Otros componentes: 82 tests ✅
- **Total: ~105-110 tests ✅**

**4.2. Verificar Separation of Concerns**
- [ ] FermentationRepository NO tiene código relacionado con samples
- [ ] SampleRepository tiene TODA la lógica de samples
- [ ] No hay duplicación entre repositorios
- [ ] Cada repositorio es responsable de SU agregado

---

## 🚀 Ejecución

### Orden de Implementación:

1. ✅ **Documentar decisión** (ADR-003 Addendum)
2. 🔄 **Fase 1:** Actualizar interfaces
3. 🔄 **Fase 2:** Refactorizar FermentationRepository
4. 🔄 **Fase 3:** Implementar SampleRepository (TDD)
5. 🔄 **Fase 4:** Validación completa

### Tiempo Estimado:
- Fase 1: 15 minutos ✅
- Fase 2: 30 minutos
- Fase 3: 2-3 horas (implementación + tests)
- Fase 4: 15 minutos

**Total:** ~3-4 horas

---

## 📊 Métricas de Éxito

### Antes:
- FermentationRepository: 7 métodos (2 de samples ❌)
- SampleRepository: ❌ NO EXISTE
- Tests: 13 (5 mezclados con samples ❌)
- Separation of Concerns: ⚠️ VIOLADO

### Después:
- FermentationRepository: 5 métodos (SOLO fermentation ✅)
- SampleRepository: 10 métodos (TODA la lógica de samples ✅)
- Tests FermentationRepository: 8 ✅
- Tests SampleRepository: ~15-20 ✅
- Separation of Concerns: ✅ APLICADO

---

## 🎓 Principios Aplicados

1. **Single Responsibility Principle**
   - Cada repositorio: UNA razón para cambiar

2. **Separation of Concerns**
   - FermentationRepository: Fermentation lifecycle
   - SampleRepository: Sample operations

3. **Don't Repeat Yourself (DRY)**
   - Sin duplicación de lógica de samples

4. **Dependency Inversion Principle**
   - Services dependen de abstracciones específicas

5. **Interface Segregation Principle**
   - Interfaces cohesivas, no fat interfaces

---

## 📝 Notas

- Breaking changes son necesarios para arquitectura limpia
- Tests actualizados reflejan responsabilidades correctas
- Migración de service layer será necesaria después
- Documentación actualizada en cada paso

---

**Estado:** 🔄 Fase 1 en progreso  
**Next Step:** Actualizar test_fermentation_repository_interface.py
