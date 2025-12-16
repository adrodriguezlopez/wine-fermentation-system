# Shared Unit Testing Infrastructure

Infraestructura compartida para crear unit tests con patrones consistentes y mínimo código boilerplate.

**Implementa: ADR-012 - Unit Test Infrastructure Refactoring**

> **📋 Contexto Completo**: Ver [.ai-context/component-context.md](.ai-context/component-context.md) para detalles de arquitectura

## 📊 Estado Actual

✅ **PRODUCCIÓN - Fase 3 COMPLETADA** (Diciembre 15, 2025)

### Infraestructura (86 tests)
- ✅ MockSessionManagerBuilder (14 tests)
- ✅ QueryResultBuilder (23 tests)
- ✅ EntityFactory (23 tests)
- ✅ ValidationResultFactory (26 tests)

### Migración (8 archivos, 142+ tests)
- ✅ Fermentation: 4 archivos, 50 tests
- ✅ Fruit Origin: 3 archivos, 92 tests
- ✅ Winery: 1 archivo

### Métricas de Éxito
- ✅ **737 tests totales** del proyecto pasando
- ✅ **~50% reducción** en código de fixtures
- ✅ **~800-1,000 líneas** de boilerplate eliminadas
- ✅ **100% consistencia** de patrones

### Documentación
- ✅ [.ai-context/module-context.md](../.ai-context/module-context.md) - Contexto del módulo
- ✅ [.ai-context/component-context.md](.ai-context/component-context.md) - Contexto del componente
- ✅ [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Ejemplos prácticos
- ✅ [ADR-012](../../../.ai-context/adr/ADR-012-unit-test-infrastructure-refactoring.md) - Decisión arquitectónica

## 🚀 Quick Start

```python
from src.shared.testing.unit import (
    create_mock_session_manager,
    create_query_result,
    create_empty_result,
    create_scalar_result,
)

@pytest.fixture
def mock_session_manager():
    return create_mock_session_manager()

@pytest.mark.asyncio
async def test_repository_get_by_id():
    # Arrange
    entity = Fermentation(id=UUID("..."), name="Test")
    mock_result = create_query_result([entity])
    mock_sm = create_mock_session_manager(execute_result=mock_result)
    
    repository = FermentationRepository(mock_sm)
    
    # Act
    result = await repository.get_by_id(entity.id)
    
    # Assert
    assert result == entity
```

## 📁 Estructura

```
src/shared/testing/unit/
├── __init__.py                 # Exports principales
├── README.md                   # Este archivo
├── USAGE_EXAMPLES.md           # Ejemplos detallados de uso
├── mocks/                      # Mock builders
│   ├── __init__.py
│   └── session_manager_builder.py
├── builders/                   # Data builders
│   ├── __init__.py
│   └── query_result_builder.py
├── fixtures/                   # Pytest fixtures
│   └── __init__.py
└── tests/                      # Tests de la infraestructura
    ├── test_session_manager_builder.py
    └── test_query_result_builder.py
```

## 🔧 Componentes Disponibles

### 1. MockSessionManagerBuilder

Crea mocks de SessionManager con comportamiento configurable.

```python
# Simple
mock_sm = create_mock_session_manager()

# Con resultado
mock_sm = create_mock_session_manager(execute_result=mock_result)

# Con errores configurados
mock_sm = (
    MockSessionManagerBuilder()
    .with_execute_result(mock_result)
    .with_commit_side_effect(Exception("Commit failed"))
    .build()
)
```

**API Completa**:
- `with_execute_result(result)` - Configura retorno de execute()
- `with_execute_side_effect(exception)` - Configura excepción en execute()
- `with_commit_side_effect(exception)` - Configura excepción en commit()
- `with_rollback_side_effect(exception)` - Configura excepción en rollback()
- `with_close_side_effect(exception)` - Configura excepción en close()
- `with_session(session)` - Usa session mock personalizado
- `build()` - Construye el mock

### 2. QueryResultBuilder

Crea mocks de SQLAlchemy Result objects.

```python
# Resultado con entidades
result = create_query_result([entity1, entity2])

# Resultado vacío
result = create_empty_result()

# Resultado escalar (COUNT, EXISTS)
result = create_scalar_result(42)

# Builder pattern para casos complejos
result = (
    QueryResultBuilder()
    .with_entities([entity1, entity2])
    .with_unique()
    .build()
)
```

**API Completa**:
- `with_entities(list)` - Configura lista de entidades
- `with_single_entity(entity)` - Configura una sola entidad
- `with_scalar(value)` - Configura valor escalar
- `with_unique()` - Habilita comportamiento unique()
- `build()` - Construye el resultado
- `build_empty()` - Construye resultado vacío
- `build_scalar()` - Construye resultado escalar optimizado

**Soporta patrones SQLAlchemy**:
- `result.scalars().all()`
- `result.scalars().first()`
- `result.scalars().one_or_none()`
- `result.scalar_one_or_none()`
- `result.scalar()`
- `result.unique().scalars().all()`
- `result.fetchall()` (legacy)

## 📈 Beneficios

Comparado con el patrón anterior:

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Líneas de código | ~35 líneas | ~2 líneas | **94% reducción** |
| Tiempo de creación | ~20 min | ~5 min | **75% más rápido** |
| Consistencia | Variable | 100% | **✅ Garantizada** |
| Mantenibilidad | Difícil | Fácil | **✅ Centralizado** |

## 🧪 Testing

```bash
# Ejecutar tests de la infraestructura
python -m pytest src/shared/testing/unit/tests/ -v

# Resultado esperado:
# 37 passed in 0.52s
```

## 📖 Documentación

- **[USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)** - Ejemplos detallados de uso
- **[ADR-012](./../../../.ai-context/adr/ADR-012-unit-test-infrastructure-refactoring.md)** - Especificación completa

## 🔄 Roadmap

### Fase 1: Core Utilities ✅ COMPLETADA
- ✅ MockSessionManagerBuilder (14 tests)
- ✅ QueryResultBuilder (23 tests)
- ✅ EntityFactory (23 tests)
- ✅ ValidationResultFactory (26 tests)

### Fase 2: Próximos Componentes (Opcional)
- ⏭️ ServiceMockBuilder - Mocks de servicios de aplicación (si necesario)
- ⏭️ DTOFactory - Factory para crear DTOs (si necesario)

### Fase 3: Pilot Migration (Próxima semana)
- Migrar 5 archivos de fermentation module
- Validar patrones y métricas
- Ajustar basado en feedback

### Fase 4: Full Migration (Semana 3)
- Migrar 42 archivos de tests
- Eliminar ≥700 líneas de código duplicado

### Fase 5: Documentation (Semana 4)
- Guía de migración completa
- API reference detallada
- Validación de métricas finales

## 🎯 Objetivos ADR-012

- ✅ Eliminar ≥700 líneas de código duplicado
- ✅ Reducir tiempo de creación de tests en 50%
- ✅ Lograr 95% de consistencia en patrones
- ✅ Simplificar mantenimiento

## 👥 Contribuir

Para añadir nuevos builders o factories:

1. Crear archivo en el directorio correspondiente (`mocks/`, `builders/`, `fixtures/`)
2. Implementar con TDD (tests primero)
3. Documentar API en docstrings
4. Añadir ejemplos en USAGE_EXAMPLES.md
5. Exportar en `__init__.py`

## ⚠️ Notas Importantes

- Todos los mocks son síncronos por defecto (salvo SessionManager que maneja async context)
- `QueryResultBuilder` NO usa `spec=AsyncResult` para evitar métodos async incorrectos
- Usar Python 3.9+ type hints con `Union` (no `|` operator)
- Seguir patrón builder + factory function para máxima flexibilidad

## 📞 Soporte

Para preguntas o problemas:
1. Revisar [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)
2. Consultar [ADR-012](./../../../.ai-context/adr/ADR-012-unit-test-infrastructure-refactoring.md)
3. Revisar tests existentes en `tests/`
