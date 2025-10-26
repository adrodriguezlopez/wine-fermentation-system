# ADR-002: Repository Architecture

**Status:** ✅ Implemented  
**Date:** 2025-09-25  
**Authors:** Development Team  
**Related ADRs:** ADR-001 (Fruit Origin Model), ADR-003 (Repository Separation)

> **📋 Context Files:**
> - [Architectural Guidelines](../../ARCHITECTURAL_GUIDELINES.md)

---

## Context

Con la introducción de `winery_id` (multi-tenant) y blends multi-lot (ADR-001), necesitamos definir:
- ¿Habrá BaseRepository?
- ¿Cómo manejar transacciones y errores?
- ¿Cómo mantener boundaries del dominio?

---

## Decision

### 1. Ports & Adapters pattern
- Cada agregado define su interfaz
- NO generic repository de dominio
- Interfaces específicas: `IFermentationRepository`, `ISampleRepository`

### 2. BaseRepository (infrastructure helper)
- Helpers técnicos: session, errores, soft-delete
- NO lógica de negocio ni invariantes
- Mapeo centralizado de errores DB

### 3. Unit of Work (UoW)
- Async context manager para transacciones
- Uso en blends y operaciones bulk
- Rollback automático en errores

### 4. Multi-tenancy scoping
- `winery_id` obligatorio en todas las queries
- Scoping a nivel de repositorio

### 5. Optimistic locking
- Campo `version` en Fermentation
- Prevención de conflictos concurrentes

### 6. Query patterns
- **SampleRepository**: Time-series queries
- **FermentationRepository**: Lifecycle operations
- **ReadModels**: Reporting optimizado (DTOs)

### 7. Error mapping
- Centralizado en BaseRepository
- Database errors → Domain errors
- `IntegrityError` → `DuplicateEntityError`

### 8. Soft-delete
- Samples con `is_deleted`
- Filtrado automático en queries

### 9. Cross-boundary access
- `HarvestLot`: Read-only repository
- No updates desde fermentation module

### 10. Return types
- Repositories retornan entidades de dominio
- `Fermentation`, `BaseSample` (no primitivos)

---

## Implementation Notes

```
src/modules/fermentation/
├── domain/
│   └── interfaces/
│       ├── fermentation_repository_interface.py
│       └── sample_repository_interface.py
└── repository_component/
    ├── repositories/
    │   ├── base_repository.py
    │   ├── fermentation_repository.py
    │   └── sample_repository.py
    └── unit_of_work.py
```

**Responsabilidades:**
- **BaseRepository**: Session management, error mapping, soft-delete helpers
- **FermentationRepository**: Lifecycle, optimistic locking
- **SampleRepository**: Time-series, upsert, bulk operations
- **ReadModels**: Reporting queries (returns DTOs)

---

## Consequences

### ✅ Benefits
- Claridad de boundaries
- Reuso técnico sin contaminar dominio
- Transacciones correctas
- Alta testabilidad
- Multi-tenant ready
- SOLID compliance
- Clean Architecture

### ⚠️ Trade-offs
- Más clases y boilerplate
- Interface overhead en escenarios simples
- Consultas complejas requieren ReadModels

### ❌ Limitations
- No generic repository (cada agregado su interfaz)
- Cross-module updates prohibidos (read-only)

---

## Quick Reference

**Repository Pattern:**
- No generic repo → Interfaz específica por agregado
- BaseRepository → Helpers técnicos solamente
- UoW async → Transacciones multi-operación
- Return entities → No primitivos

**Multi-tenancy:**
- `winery_id` obligatorio en queries
- Scoping a nivel repositorio

**Soft-delete:**
- Samples: `is_deleted = True`
- Filtrado automático en queries

**Cross-boundaries:**
- `HarvestLot`: Read-only desde fermentation module

**SOLID Principles:**
- **SRP**: BaseRepository (technical) vs Domain repos (business)
- **OCP**: Extensible via interfaces
- **LSP**: Implementations substitutable
- **ISP**: Specific interfaces per aggregate
- **DIP**: Depend on abstractions (ISessionManager, IDatabaseConfig)

---

## Status

✅ **Accepted** - Implemented with 110+ tests passing
