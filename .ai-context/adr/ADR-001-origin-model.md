# ADR-001: Modelo de Origen de Fruta (Winery → Vineyard → Block → HarvestLot)

**Status:** Accepted  
**Date:** 2025-09-25  
**Authors:** Arquitectura de Fermentación (VintArch)  

---

## Context
Actualmente, el modelo solo contempla la entidad `Fermentation`. No existe una forma clara de saber **de qué viñedo o bloque proviene la fruta** utilizada en cada fermentación.  
En el mundo real, la trazabilidad es crítica:  
- Una **Winery** (bodega) tiene varios **Vineyards** (viñedos).  
- Cada vineyard se subdivide en **Blocks** (parcelas), cada uno con características de terroir distintas (suelo, pendiente, insolación).  
- Durante la vendimia, la uva se cosecha en cada block en fechas concretas.  
- Estas cosechas se representan como **HarvestLots**.  
- Una fermentación puede usar uno o varios lots (mezclas o *blends*).  

Necesitamos representar esta jerarquía y asegurar trazabilidad vino → fermentación → lots → block → vineyard → winery.

---

## Decision
1. **MVP mono-bodega, pero preparado para multi-bodega**:  
   - Todas las tablas llevan `winery_id`.  
   - En MVP habrá solo una bodega, pero el modelo soporta varias.  

2. **Nuevas entidades y relaciones**:  
   - `Winery` (1) ──► (N) `Vineyard` ──► (N) `VineyardBlock` ──► (N) `HarvestLot`.  
   - `Fermentation` mantiene su rol de agregado raíz.  
   - Nueva entidad de asociación: `FermentationLotSource`, que relaciona `Fermentation` con uno o varios `HarvestLot`.  

3. **Fuente de verdad**:  
   - En `FermentationLotSource` guardamos `mass_used_kg`.  
   - El porcentaje se **calcula** en consultas (`mass_used_kg / fermentation.input_mass_kg`), no se persiste como campo principal.  

4. **Invariantes de negocio (reglas obligatorias)**:  
   - La suma de todas las masas (`mass_used_kg`) en un fermentation = `fermentation.input_mass_kg`.  
   - Cada `mass_used_kg > 0`.  
   - No se repite el mismo `HarvestLot` en la misma fermentación.  
   - Todos los lots asociados a una fermentación pertenecen a la **misma winery**.  
   - La fecha de cosecha (`HarvestLot.harvest_date`) debe ser ≤ la fecha de inicio de la fermentación (`Fermentation.start_date`).  

5. **DB Constraints (SQL/ORM)**:  
   - UNIQUE `(vineyard.code, winery_id)`  
   - UNIQUE `(block.code, vineyard_id)`  
   - UNIQUE `(harvest_lot.code, winery_id)`  
   - FK `FermentationLotSource.fermentation_id → Fermentation.id`  
   - FK `FermentationLotSource.harvest_lot_id → HarvestLot.id`  
   - CHECK `mass_used_kg > 0`  
   - Índice sugerido: `HarvestLot(winery_id, harvest_date)`  

---

## Entity-Relationship Diagram (ERD)

```
Winery (1) ───< Vineyard (N) ───< VineyardBlock (N) ───< HarvestLot (N)
   │                                                   \
   │                                                    \
   └───────────────────────────────────────────────────── Fermentation (N)
                                                          │
                                                          └──< FermentationLotSource (N)

TABLAS CLAVE
------------
Winery
- id (PK)
- name

Vineyard
- id (PK), winery_id (FK → Winery.id)
- code (UNIQUE por winery)
- name

VineyardBlock
- id (PK), vineyard_id (FK → Vineyard.id)
- code (UNIQUE por vineyard)
- soil, slope, notes

HarvestLot
- id (PK), winery_id (FK → Winery.id), block_id (FK → VineyardBlock.id)
- code (UNIQUE por winery)
- harvest_date, weight_kg, brix, notes

Fermentation
- id (PK), winery_id (FK → Winery.id)
- start_date, input_mass_kg, ...

FermentationLotSource
- id (PK)
- fermentation_id (FK → Fermentation.id)
- harvest_lot_id (FK → HarvestLot.id)
- mass_used_kg (CHECK > 0)
```
---

## Consequences

**Positivas**  
- ✅ Trazabilidad completa de la fruta usada en cada vino.  
- ✅ Soporte natural para blends (una fermentación con varios lots).  
- ✅ Flexibilidad para validaciones por terroir (ej. °Brix inicial por viñedo o bloque).  
- ✅ Preparado para multi-bodega sin afectar el MVP actual.  

**Negativas**  
- ⚠️ Introducimos 4 entidades nuevas (`Winery`, `Vineyard`, `VineyardBlock`, `HarvestLot`) + tabla de unión `FermentationLotSource`.  
- ⚠️ Endpoints y queries más complejos (joins + validación de invariantes).  
- ⚠️ Se requiere transaccionalidad (UoW) para operaciones de mezcla.  

---

## Status
- **Accepted**  

---

## Links
- [Project Context](../project-context.md)  
- [Domain Model Guide](../domain-model-guide.md)  
