# Wine Fermentation System - Project Structure Map

**Last Update:** October 25, 2025  
**Purpose:** Navigation map for project structure and implementation status

---

## 📁 Core Structure

```
wine-fermentation-system/
├── .ai-context/                              # ADRs y contexto
│   ├── adr/                                  # Architecture Decision Records
│   │   ├── ADR-001-folder-structure.md
│   │   ├── ADR-002-repositories-architecture/
│   │   ├── ADR-003-repository-interface-refactoring.md
│   │   ├── ADR-004-harvest-module-consolidation.md
│   │   ├── ADR-005-service-layer-interfaces.md
│   │   └── ADR-INDEX.md
│   ├── project-context.md                    # System-level context
│   ├── ARCHITECTURAL_GUIDELINES.md           # SOLID + Clean Architecture
│   └── PROJECT_STRUCTURE_MAP.md              # This file
│
├── src/
│   ├── shared/infra/                         # Shared infrastructure
│   │   ├── database/                         # ✅ DB config & sessions
│   │   ├── interfaces/                       # ✅ Protocols (DIP)
│   │   ├── orm/                              # ✅ BaseEntity
│   │   └── repository/                       # ✅ BaseRepository
│   │
│   └── modules/
│       ├── fermentation/                     # 🍷 Fermentation Module
│       │   ├── src/
│       │   │   ├── domain/                   # ✅ Entities, DTOs, Enums, Interfaces
│       │   │   │   ├── entities/             # Fermentation, BaseSample, User
│       │   │   │   ├── dtos/                 # FermentationCreate, SampleCreate
│       │   │   │   ├── enums/                # FermentationStatus, SampleType
│       │   │   │   └── repositories/         # IFermentationRepository, ISampleRepository
│       │   │   │
│       │   │   ├── repository_component/     # ✅ Repository implementations
│       │   │   │   ├── repositories/
│       │   │   │   │   ├── fermentation_repository.py  # ✅ COMPLETE
│       │   │   │   │   └── sample_repository.py        # ✅ COMPLETE
│       │   │   │   └── errors.py             # Repository exceptions
│       │   │   │
│       │   │   └── service_component/        # ✅ Service Layer
│       │   │       ├── interfaces/           # Service interfaces
│       │   │       │   ├── fermentation_service_interface.py   # ✅ 7 methods
│       │   │       │   ├── fermentation_validator_interface.py # ✅ 3 methods
│       │   │       │   ├── sample_service_interface.py         # ✅ 6 methods
│       │   │       │   └── validation_orchestrator_interface.py
│       │   │       ├── services/             # Service implementations
│       │   │       │   ├── fermentation_service.py    # ✅ COMPLETE (410 lines)
│       │   │       │   └── sample_service.py          # ✅ COMPLETE (460 lines)
│       │   │       ├── validators/
│       │   │       │   ├── fermentation_validator.py  # ✅ COMPLETE (175 lines)
│       │   │       │   └── validation_orchestrator.py
│       │   │       └── errors.py             # Service exceptions
│       │   │
│       │   └── tests/                        # ✅ 182 tests passing
│       │       ├── unit/                     # 173 tests
│       │       │   ├── fermentation_lifecycle/        # 33 service tests
│       │       │   ├── sample_lifecycle/              # 27 service tests
│       │       │   ├── validators/                    # 12 validator tests
│       │       │   ├── repository_component/          # 39 repo tests
│       │       │   └── validation/                    # 53 validation tests
│       │       └── integration/              # 9 tests
│       │
│       ├── fruit_origin/                     # 🍇 Fruit Origin Module
│       │   └── src/domain/entities/
│       │       ├── vineyard.py               # ✅ Vineyard entity
│       │       ├── vineyard_block.py         # ✅ VineyardBlock entity
│       │       └── harvest_lot.py            # ✅ HarvestLot entity (19 fields)
│       │
│       └── winery/                           # 🏭 Winery Module
│           └── src/domain/entities/
│               └── winery.py                 # ✅ Winery entity
│
├── docker-compose.yml                        # ✅ PostgreSQL setup
└── recreate_test_tables.py                  # ✅ DB tables creator
```

---

## 🎯 Implementation Status (Oct 25, 2025)

### ✅ COMPLETE

| Component | Tests | Status |
|-----------|-------|--------|
| **Domain Layer** | N/A | ✅ Entities, DTOs, Enums, Interfaces |
| **Repository Layer** | 110 | ✅ FermentationRepository + SampleRepository |
| **Service Layer** | 72 | ✅ FermentationService + SampleService + Validators |
| **Validation Layer** | 53 | ✅ ValidationOrchestrator + Value/Business/Chronology validators |
| **Infrastructure** | 18 | ✅ Database config + Sessions + BaseRepository |
| **TOTAL** | **182** | ✅ **ALL PASSING** |

### 🔄 IN PROGRESS

| Component | Status |
|-----------|--------|
| **API Layer** | 🔄 Next phase - FastAPI endpoints |

---

## 🗄️ Database Schema (9 Tables)

| Table | Module | Purpose |
|-------|--------|---------|
| `users` | fermentation | User authentication |
| `wineries` | winery | Winery information |
| `vineyards` | fruit_origin | Vineyard top-level |
| `vineyard_blocks` | fruit_origin | Vineyard parcels |
| `harvest_lots` | fruit_origin | Harvested fruit (19 fields) |
| `fermentations` | fermentation | Fermentation process (with `is_deleted`) |
| `fermentation_lot_sources` | fermentation | Links fermentation → lots |
| `samples` | fermentation | Measurements (single-table inheritance) |
| `fermentation_notes` | fermentation | Log entries |

---

## 📊 Test Coverage Summary

```
Total: 182/182 tests passing (100%)

Repository Layer (110 tests):
├── FermentationRepository: 8 integration + unit tests
├── SampleRepository: 12 interface + 1 integration tests
├── Error handling: 19 tests
└── Validation: 53 tests (orchestrator + validators)

Service Layer (72 tests):
├── FermentationService: 33 tests (7 methods)
├── FermentationValidator: 12 tests (3 methods)
└── SampleService: 27 tests (6 methods)
```

---

## 🔗 Key ADRs

- **ADR-001**: Fruit Origin Model (Winery → Vineyard → Block → HarvestLot)
- **ADR-002**: Repository Architecture (BaseRepository + patterns)
- **ADR-003**: Repository Separation of Concerns (Fermentation ≠ Sample)
- **ADR-004**: Harvest Module Consolidation (fruit_origin consolidation)
- **ADR-005**: Service Layer Interfaces (Type safety + SOLID)

---

## 🚀 Next Steps

1. **API Layer**: FastAPI endpoints for services
2. **Integration Tests**: End-to-end workflow tests
3. **Authentication**: User management
4. **Frontend**: Web interface

---

## 📝 Quick Navigation

**Need to work on:**
- Domain entities → `src/modules/{module}/src/domain/entities/`
- Repository interfaces → `src/modules/{module}/src/domain/repositories/`
- Repository implementations → `src/modules/{module}/src/repository_component/repositories/`
- Service interfaces → `src/modules/{module}/src/service_component/interfaces/`
- Service implementations → `src/modules/{module}/src/service_component/services/`
- Tests → `src/modules/{module}/tests/`
- ADRs → `.ai-context/adr/`

**Documentation:**
- System context → `.ai-context/project-context.md`
- Architecture → `.ai-context/ARCHITECTURAL_GUIDELINES.md`
- This map → `.ai-context/PROJECT_STRUCTURE_MAP.md`
