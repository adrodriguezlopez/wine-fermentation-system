# ADR-004: Harvest Module Consolidation & SQLAlchemy Registry Fix

**Status:** ✅ Implemented  
**Date:** 2025-10-05  
**Deciders:** Development Team  
**Related ADRs:** ADR-001 (Folder Structure), ADR-003 (Repository Refactoring)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

Durante tests de integración se descubrieron dos problemas:

1. **Duplicación de HarvestLot**: Existían dos módulos (`harvest/` y `fruit_origin/`) con la misma entidad
2. **SQLAlchemy Registry Conflicts**: Error "Multiple classes found" por paths ambiguos en relationships

---

## Decision

### 1. Consolidación de módulos

**Acción:** Eliminar `src/modules/harvest/` y usar exclusivamente `src/modules/fruit_origin/`

**Razón:**
- `fruit_origin` es el bounded context correcto (Vineyard → VineyardBlock → HarvestLot)
- HarvestLot de fruit_origin tiene trazabilidad completa (19 campos vs 5)
- Relaciones y constraints adecuados para multi-tenancy

### 2. Fix de SQLAlchemy Registry

**Estrategias implementadas:**

**2.1 Fully-qualified paths en relationships:**
```python
# ✅ Paths completos
relationship("src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample")
```

**2.2 Relationships unidireccionales con herencia:**
```python
# BaseSample (single-table inheritance)
fermentation: Mapped["Fermentation"] = relationship(..., viewonly=True)

# Fermentation (sin back_populates para evitar conflictos)
samples: Mapped[List["BaseSample"]] = relationship(...)
```

**2.3 Usar flush() en vez de commit() en tests:**
```python
await db_session.flush()  # Asigna IDs sin cerrar transacción
# Context manager hace rollback automático
```

---

## Implementation Notes

**Módulos consolidados:**
```
src/modules/fruit_origin/
├── domain/
│   └── entities/
│       ├── vineyard.py
│       ├── vineyard_block.py
│       └── harvest_lot.py          # Único HarvestLot
└── repository_component/
    └── harvest_lot_repository.py

❌ ELIMINADO: src/modules/harvest/
```

**Cambios en SQLAlchemy:**
- Todos los relationships usan fully-qualified paths
- Single-table inheritance usa relationships unidireccionales
- Tests usan flush() para mantener transacciones abiertas

---

## Consequences

### ✅ Benefits
- Arquitectura limpia: Un bounded context para origen del fruto
- No más duplicación de HarvestLot
- Registry conflicts resueltos
- Tests de integración funcionando

### ⚠️ Trade-offs
- Paths más largos en relationship declarations
- Algunos relationships son unidireccionales (design constraint)

### ❌ Limitations
- Breaking changes para código que usaba `src/modules/harvest/`
- Requiere actualizar imports en todo el proyecto

---

## Quick Reference

**Bounded Context:**
- `fruit_origin`: Vineyard → VineyardBlock → HarvestLot ✅
- ~~`harvest`~~: Eliminado ❌

**SQLAlchemy Best Practices:**
- Fully-qualified paths en relationships
- Unidirectional relationships con herencia polimórfica
- flush() en tests, no commit()

**Multi-tenancy:**
- `UniqueConstraint('code', 'winery_id')` en HarvestLot
- Winery scoping en todas las queries

---

## Status

✅ **Accepted** - Implementado, tests de integración passing
