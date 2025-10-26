# ADR-001: Fruit Origin Model (Winery → Vineyard → Block → HarvestLot)

**Status:** ✅ Implemented  
**Date:** 2025-09-25  
**Authors:** Development Team  
**Related ADRs:** ADR-004 (Harvest Module Consolidation)

> **📋 Context Files:**
> - [Architectural Guidelines](../../ARCHITECTURAL_GUIDELINES.md)

---

## Context

El modelo original solo tenía `Fermentation` sin trazabilidad del origen de la fruta. En la realidad:
- Una **Winery** (bodega) tiene **Vineyards** (viñedos)
- Cada vineyard tiene **Blocks** (parcelas con terroir específico)
- Las cosechas se representan como **HarvestLots**
- Una fermentación puede usar múltiples lots (blends)

Necesitamos representar esta jerarquía para trazabilidad completa.

---

## Decision

### 1. Jerarquía de entidades

**Estructura:**
```
Winery (1) → Vineyard (N) → VineyardBlock (N) → HarvestLot (N)
                                                      ↓
                                              Fermentation (N)
                                                      ↓
                                          FermentationLotSource (N)
```

### 2. Multi-tenancy preparado (MVP single-tenant)
- Todas las tablas con `winery_id`
- MVP usa una bodega, modelo soporta múltiples

### 3. Asociación Fermentation-HarvestLot
- `FermentationLotSource`: Tabla de asociación
- `mass_used_kg`: Masa real usada por lot
- Porcentaje se **calcula** (`mass_used_kg / input_mass_kg`), no se persiste

### 4. Invariantes de negocio
- Σ `mass_used_kg` = `fermentation.input_mass_kg`
- `mass_used_kg > 0` para cada lot
- No duplicar lots en misma fermentación
- Todos los lots de una fermentación de la misma winery
- `harvest_date ≤ fermentation.start_date`

### 5. DB Constraints
- `UNIQUE(vineyard.code, winery_id)`
- `UNIQUE(block.code, vineyard_id)`
- `UNIQUE(harvest_lot.code, winery_id)`
- `CHECK(mass_used_kg > 0)`
- FKs: fermentation_id, harvest_lot_id

---

## Implementation Notes

**Entidades principales:**
```
Winery
├── id, name

Vineyard
├── id, winery_id (FK)
├── code (UNIQUE per winery)
└── name

VineyardBlock
├── id, vineyard_id (FK)
├── code (UNIQUE per vineyard)
└── soil, slope, notes

HarvestLot
├── id, winery_id (FK), block_id (FK)
├── code (UNIQUE per winery)
├── harvest_date, weight_kg, brix
└── notes

FermentationLotSource (association)
├── id, fermentation_id (FK), harvest_lot_id (FK)
└── mass_used_kg (CHECK > 0)
```

**Ubicación:** `src/modules/fruit_origin/` (ver ADR-004)

---

## Consequences

### ✅ Benefits
- Trazabilidad completa (vino → lots → blocks → vineyards)
- Multi-tenancy preparado
- Soporte para blends (múltiples lots)
- Modelo escalable

### ⚠️ Trade-offs
- Mayor complejidad del modelo
- Validaciones de negocio más complejas
- Porcentajes calculados (no persistidos)

### ❌ Limitations
- Requiere service layer para validar invariantes
- Suma de masas debe validarse en cada operación

---

## Quick Reference

**Bounded Context:** `fruit_origin`

**Trazabilidad:**
```
Wine → Fermentation → FermentationLotSource → HarvestLot → 
       VineyardBlock → Vineyard → Winery
```

**Business Rules:**
- Σ masses = input_mass
- No duplicate lots per fermentation
- Same winery for all lots
- harvest_date ≤ start_date

**Indexes:**
- `HarvestLot(winery_id, harvest_date)` para queries temporales

---

## Status

✅ **Accepted** - Modelo implementado en `src/modules/fruit_origin/`
