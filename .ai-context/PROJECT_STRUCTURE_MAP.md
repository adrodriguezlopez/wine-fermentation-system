# Wine Fermentation System - Project Structure Map

**Fecha de actualización:** 2025-10-05  
**Propósito:** Mapa de navegación para evitar confusión en implementaciones  
**Última refactorización:** ADR-004 (Harvest Module Consolidation & SQLAlchemy Registry Fix) - 2025-10-05

---

## 🗂️ Estructura del Proyecto

```
wine-fermentation-system/
├── .ai-context/                              # Documentación ADR y contexto
│   ├── adr/
│   │   ├── ADR-001-folder-structure/
│   │   ├── ADR-002-repositories-architecture/
│   │   ├── ADR-003-repository-interface-refactoring.md
│   │   ├── ADR-004-harvest-module-consolidation.md  # ✅ NUEVO
│   │   ├── ADR-INDEX.md                      # ✅ NUEVO (índice de ADRs)
│   │   ├── ADR-template.md
│   │   └── ADR-template-light.md
│   ├── project-context.md                    # Sistema-level context
│   ├── PROJECT_STRUCTURE_MAP.md              # 📍 ESTE ARCHIVO
│   ├── ARCHITECTURAL_GUIDELINES.md           # ✅ ACTUALIZADO (SQLAlchemy imports)
│   └── DOCUMENTATION_UPDATE_SUMMARY.md       # ✅ NUEVO (changelog)
│
├── src/
│   ├── shared/                               # 🔧 INFRAESTRUCTURA COMPARTIDA
│   │   └── infra/
│   │       ├── database/                     # ✅ Database infrastructure (COMPLETADO)
│   │       │   ├── config.py                 # → DatabaseConfig (implementa IDatabaseConfig)
│   │       │   ├── session.py                # → DatabaseSession (implementa ISessionManager)
│   │       │   └── __init__.py
│   │       ├── interfaces/                   # ✅ Protocols/Interfaces (COMPLETADO)
│   │       │   ├── database_config.py        # → IDatabaseConfig protocol
│   │       │   ├── session_manager.py        # → ISessionManager protocol
│   │       │   └── __init__.py
│   │       ├── orm/                          # ✅ ORM base (COMPLETADO)
│   │       │   ├── base_entity.py            # → BaseEntity (imports consistentes)
│   │       │   └── __init__.py
│   │       ├── test/                         # ✅ Tests de infraestructura (COMPLETADO)
│   │       │   ├── database/
│   │       │   │   ├── test_interfaces.py    # → Tests de compliance (7 tests ✅)
│   │       │   │   ├── test_session.py       # → Tests funcionales (11 tests ✅)
│   │       │   │   ├── check_db_connection.py
│   │       │   │   └── __init__.py
│   │       │   └── __init__.py
│   │       └── __init__.py
│   │
│   └── modules/
│       ├── fermentation/                     # 🍷 MÓDULO DE FERMENTACIÓN
│       │   ├── .ai-context/
│       │   │   └── module-context.md         # Module-level context
│       │   ├── src/
│       │   │   ├── domain/
│       │   │   │   ├── .ai-context/
│       │   │   │   │   └── component-context.md  # Domain layer context
│       │   │   │   ├── entities/             # ✅ Domain entities (COMPLETADO)
│       │   │   │   │   ├── fermentation.py   # → Fermentation (fully-qualified paths)
│       │   │   │   │   ├── samples/
│       │   │   │   │   │   ├── base_sample.py  # → BaseSample (viewonly=True)
│       │   │   │   │   │   ├── wine_sample.py
│       │   │   │   │   │   └── juice_sample.py
│       │   │   │   │   ├── fermentation_note.py
│       │   │   │   │   ├── fermentation_lot_source.py
│       │   │   │   │   └── user.py
│       │   │   │   │
│       │   │   │   └── repositories/         # ✅ Domain interfaces (COMPLETADO)
│       │   │   │       ├── fermentation_repository_interface.py  # → IFermentationRepository
│       │   │   │       └── sample_repository.py  # → SampleRepository (concrete)
│       │   │   │
│       │   │   ├── repository_component/     # ✅ Repository infrastructure (COMPLETADO)
│       │   │   │   ├── errors.py             # → Error handling (19 tests ✅)
│       │   │   │   ├── repositories/
│       │   │   │   │   └── fermentation_repository.py  # → Concrete implementation
│       │   │   │   └── __init__.py
│       │   │   │
│       │   │   └── service_component/        # Service layer
│       │   │       └── interfaces/
│       │   │           ├── fermentation_read_service.py
│       │   │           └── sample_read_service.py
│       │   │
│       │   └── tests/                        # ✅ Tests del módulo (103 tests ✅)
│       │       ├── unit/                     # 102 tests ✅
│       │       │   ├── repository_component/
│       │       │   ├── repositories/
│       │       │   ├── entities/
│       │       │   └── conftest.py
│       │       └── integration/              # 1 test ✅
│       │           ├── conftest.py           # → Fixtures: vineyard, block, harvest_lot
│       │           └── test_fermentation_lifecycle.py
│       │
│       ├── fruit_origin/                     # 🍇 MÓDULO DE ORIGEN DEL FRUTO (✅ CONSOLIDADO)
│       │   ├── .ai-context/
│       │   │   └── module-context.md         # ✅ NUEVO
│       │   └── src/
│       │       └── domain/
│       │           ├── .ai-context/
│       │           │   └── component-context.md  # ✅ NUEVO (Domain layer)
│       │           └── entities/
│       │               ├── vineyard.py       # → Vineyard (winery_id, code, name)
│       │               ├── vineyard_block.py # → VineyardBlock (11 campos técnicos)
│       │               └── harvest_lot.py    # → HarvestLot (19 campos trazabilidad)
│       │
│       ├── winery/                           # 🏭 MÓDULO DE BODEGA
│       │   ├── .ai-context/
│       │   │   └── module-context.md         # ✅ NUEVO
│       │   └── src/
│       │       └── domain/
│       │           ├── .ai-context/
│       │           │   └── component-context.md  # ✅ NUEVO (Domain layer)
│       │           └── entities/
│       │               └── winery.py         # → Winery (location, ownership)
│       │
│       ├── auth/                             # 🔐 MÓDULO DE AUTENTICACIÓN
│       ├── analysis-engine/                  # 📊 MÓDULO DE ANÁLISIS
│       ├── historical-data/                  # 📈 MÓDULO DE DATOS HISTÓRICOS
│       └── action-tracking/                  # 📝 MÓDULO DE SEGUIMIENTO DE ACCIONES
│
├── docker-compose.yml                        # ✅ Database setup (COMPLETADO)
├── recreate_test_tables.py                  # ✅ Database tables creator (9 tables)
└── README.md
```

---

## 🗄️ Database Schema

**9 Tables totales** (generadas con `poetry run python recreate_test_tables.py`):

| Table | Module | Purpose | Key Fields |
|-------|--------|---------|------------|
| `users` | fermentation | User authentication & tracking | username, email, full_name |
| `wineries` | winery | Winery location & ownership | code, name, location |
| `vineyards` | fruit_origin | Vineyard top-level | winery_id, code, name |
| `vineyard_blocks` | fruit_origin | Vineyard parcels | vineyard_id, code, soil_type, area_ha |
| `harvest_lots` | fruit_origin | Harvested fruit lots | block_id, code, harvest_date, brix_at_harvest (19 campos) |
| `fermentations` | fermentation | Fermentation process | code, batch_code, winery_id, start_date |
| `fermentation_lot_sources` | fermentation | Links fermentation → harvest_lots | fermentation_id, harvest_lot_id, weight_kg_used |
| `samples` | fermentation | Sample measurements (single-table inheritance) | fermentation_id, sample_type, ph, temperature |
| `fermentation_notes` | fermentation | Fermentation log entries | fermentation_id, recorded_by_user_id, content |

---

## 🎯 Estado Actual por Componente

### ✅ COMPLETADOS (Tests pasando)

| Component | Location | Tests | Status |
|-----------|----------|-------|---------|
| **Database Config** | `src/shared/infra/database/config.py` | ✅ | Implementa `IDatabaseConfig` |
| **Database Session** | `src/shared/infra/database/session.py` | ✅ | Implementa `ISessionManager` |
| **Interfaces** | `src/shared/infra/interfaces/` | ✅ | Protocols para DIP |
| **Error Handling** | `src/modules/fermentation/src/repository_component/errors.py` | 19 ✅ | SQLSTATE mapping |
| **Repository Interface** | `src/modules/fermentation/src/domain/repositories/fermentation_repository_interface.py` | 13 ✅ | Domain contract |
| **FermentationRepository** | `src/modules/fermentation/src/repository_component/repositories/fermentation_repository.py` | 13 ✅ | Concrete implementation |
| **SampleRepository** | `src/modules/fermentation/src/domain/repositories/sample_repository.py` | ✅ | Concrete implementation |
| **Domain Entities** | `src/modules/fermentation/src/domain/entities/` | ✅ | Fully-qualified paths, no circular imports |
| **fruit_origin Entities** | `src/modules/fruit_origin/src/domain/entities/` | ✅ | Vineyard, VineyardBlock, HarvestLot |
| **winery Entities** | `src/modules/winery/src/domain/entities/` | ✅ | Winery |

**Total Tests Passing:** 103 ✅ (102 unit + 1 integration)

### ⚠️ ELIMINADOS

| Component | Previous Location | Reason | ADR |
|-----------|-------------------|--------|-----|
| **harvest/ module** | `src/modules/harvest/` | ❌ Duplicated HarvestLot (5 fields vs 19) | ADR-004 |

### 🏆 Mejoras de ADR-004

| Improvement | Before | After |
|-------------|--------|-------|
| **HarvestLot fields** | 5 campos básicos | 19 campos con trazabilidad completa |
| **SQLAlchemy Registry** | "Multiple classes found" errors | ✅ Fully-qualified paths, no conflicts |
| **Single-Table Inheritance** | Bidirectional relationships conflict | ✅ Unidirectional with viewonly=True |
| **Test fixtures** | Missing vineyard hierarchy | ✅ test_vineyard, test_vineyard_block, test_harvest_lot |
| **Transaction management** | commit() closing transactions | ✅ flush() keeping context open |

---

## 🧭 Navegación Rápida

### Para Database Infrastructure:
```bash
cd src/shared/infra/database/
# config.py    → DatabaseConfig
# session.py   → DatabaseSession
```

### Para Repository Component:
```bash
cd src/modules/fermentation/src/repository_component/
# errors.py    → RepositoryError hierarchy
# base_repository.py (siguiente)
```

### Para Tests:
```bash
# Infrastructure tests
cd src/shared/infra/test/database/

# Module tests  
cd src/modules/fermentation/tests/unit/repository_component/
```

### Para ejecutar tests específicos:
```bash
# Database infrastructure tests
cd src/modules/fermentation
poetry run python -c "import sys; sys.path.append('../../shared/infra/test'); import pytest; pytest.main(['-v', '../../shared/infra/test/database/'])"

# Repository component tests
poetry run pytest tests/unit/repository_component/ -v
```

---

## 🏗️ Arquitectura de Interfaces

```
IDatabaseConfig (protocol)
    ↓ implements
DatabaseConfig (concrete)
    ↓ used by
ISessionManager (protocol)  
    ↓ implements
DatabaseSession (concrete)
    ↓ will be used by
IBaseRepository (protocol) ← NEXT
    ↓ implements  
BaseRepository (concrete) ← NEXT
```

---

## 📝 Notas de Implementación

### Principios SOLID Aplicados:
- **S**RP: Cada clase una responsabilidad
- **O**CP: Extensible vía interfaces
- **L**SP: Implementaciones sustituibles
- **I**SP: Interfaces específicas
- **D**IP: ✅ **Dependency Inversion implementado** (DatabaseSession ← IDatabaseConfig)

### TDD Methodology:
1. ✅ **RED**: Test fails first
2. ✅ **GREEN**: Minimum implementation to pass
3. ✅ **REFACTOR**: Clean code while keeping tests green

### Patrones Implementados:
- ✅ **Repository Pattern**: Domain interfaces + Infrastructure implementations
- ✅ **Protocol/Interface Pattern**: Typing protocols for clean contracts
- ✅ **Error Mapping Pattern**: Database exceptions → Domain exceptions
- ✅ **Single Source of Truth**: Domain entities en una ubicación canónica (Ver ADR-003)
- 🔄 **Unit of Work Pattern**: NEXT (async context manager)

### Refactoring Completado (ADR-003):
- ✅ **Imports Circulares Resueltos**: Uso correcto de imports relativos y TYPE_CHECKING
- ✅ **Eliminada Duplicación**: Todas las clases importadas desde ubicaciones canónicas
- ✅ **Interfaz Sincronizada**: Repository interface refleja modelo SQLAlchemy real
- ✅ **95/95 Tests Passing**: Validación completa del refactoring

---

## 🚀 Próximos Pasos

1. **BaseRepository Interface** → Define contract for common repository operations
2. **BaseRepository Implementation** → Session management + Error mapping + Soft delete
3. **Sample Queries (FermentationRepository)** → Implementar get_samples() + get_samples_in_range()
4. **Specific Repositories** → SampleRepository (si es necesario como repositorio independiente)
5. **Unit of Work** → Transaction management for complex operations
6. **Integration Tests** → End-to-end validation

---

## 📚 ADRs Relacionados

- **ADR-001**: Folder Structure - Module organization & bounded contexts
- **ADR-002**: Repository Architecture Pattern - Foundation for repository layer
- **ADR-003**: Repository Interface Refactoring - Circular imports resolution & interface sync (2025-10-04)
- **ADR-004**: Harvest Module Consolidation & SQLAlchemy Registry Fix - Module consolidation + import best practices (2025-10-05)

---

*Este mapa se actualiza conforme avanza la implementación. Última actualización: 2025-10-05*