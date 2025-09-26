# ADR-001: Modelo de Origen de Fruta (Winery → Vineyard → Block → HarvestLot)

**Status:** Accepted (Implementación en pausa - esperando domain services)  
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
- fermented_by_user_id (FK → User.id)
- vintage_year, yeast_strain
- input_mass_kg, initial_sugar_brix, initial_density
- vessel_code (UNIQUE por winery, opcional)
- status, start_date

FermentationLotSource
- id (PK)
- fermentation_id (FK → Fermentation.id)
- harvest_lot_id (FK → HarvestLot.id)
- mass_used_kg (CHECK > 0)
```
---

## Decisiones de Refactoring

### Campos Eliminados de Fermentation
- **`winery` (String)** → **ELIMINADO**. Usar `fermentation.winery_id` (FK → Winery.id).
- **`vineyard` (String)** → **ELIMINADO**. El viñedo se deriva de los HarvestLot asociados.
- **`grape_variety` (String)** → **ELIMINADO** del core. La(s) variedad(es) se derivan de los HarvestLot.

### Campos Agregados
- **`vessel_code: str | None`** → Campo opcional para identificar el recipiente de fermentación.
- **Constraint**: UNIQUE (winery_id, vessel_code) para evitar colisiones por bodega.

### Trade-offs y Consecuencias Críticas

**✅ Beneficios:**
- **Eliminación de duplicación**: No hay inconsistencias entre `Fermentation.grape_variety` y `HarvestLot.grape_variety`.
- **Soporte natural para blends**: Una fermentación puede tener múltiples variedades via múltiples HarvestLots.
- **Trazabilidad completa**: Toda información de origen viene de la cadena HarvestLot → VineyardBlock → Vineyard.
- **Asociación implementada**: `FermentationLotSource` permite rastrear masa específica de cada lot en fermentación.

**⚠️ Trade-offs:**
- **Queries más complejas**: Para mostrar grape_variety se requieren JOINs con HarvestLot.
- **UI temprano**: Si el UI necesita mostrar variedad antes de asignar lots, usar campo calculado/no persistido.
- **winery_id redundante en MVP**: En mono-bodega puede parecer innecesario, pero simplifica invariantes y prepara multi-tenant.
- **Gestión de blends**: La lógica para mantener balance de masas requiere validación de servicio de dominio.

## Implementación FermentationLotSource

### Diseño Técnico Implementado
- **Ubicación DDD**: Entidad en módulo `fermentation/src/domain/entities/` siguiendo principio de agregado raíz.
- **Campos mínimos**: `fermentation_id`, `harvest_lot_id`, `mass_used_kg` (obligatorios).
- **Campos opcionales**: `notes` (texto contextual), `created_at`/`updated_at` (auditoría).
- **Constraints DB**: `UNIQUE(fermentation_id, harvest_lot_id)`, `CHECK(mass_used_kg > 0)`.
- **Índices**: `idx_fermentation_lot_source_fermentation`, `idx_fermentation_lot_source_harvest_lot`.

### Razonamiento de Ubicación
- **Agregado raíz**: `Fermentation` es el root, `FermentationLotSource` existe para expresar su composición.
- **Ciclo de vida**: Depende de la fermentación (crear/actualizar/borrar en la misma UoW).
- **Consistencia transaccional**: Gobierna dentro del agregado de Fermentation.
- **Evita cruce de límites**: No rompe el subdominio `fruit_origin` que posee `HarvestLot`.

### Invariantes de Negocio (⚠️ PENDIENTE: Requiere Domain Services)
- **Balance de masas**: Σ mass_used_kg = fermentation.input_mass_kg
- **Misma bodega**: Todos los HarvestLot.winery_id = Fermentation.winery_id  
- **Fechas coherentes**: HarvestLot.harvest_date ≤ Fermentation.start_date
- **No duplicados**: UNIQUE constraint previene mismo lot en misma fermentación

**🚫 BLOQUEADOR**: Sin domain services implementados, estas reglas solo existen a nivel de constraints DB básicos. La lógica de negocio compleja requiere servicios de dominio para validación y aplicación de invariantes.

### Implementación Status 🔄
- ✅ **Entidades**: `FermentationLotSource` creada con constraints SQLAlchemy 2.0
- ✅ **Constraints DB**: Todos los UNIQUE, CHECK, FK e INDEX implementados
- ✅ **Tests**: Metadatos y lógica de blend implementados (63 tests pasando)
- ✅ **Relationships**: Bidireccionales entre Fermentation ↔ FermentationLotSource activadas
- 🔄 **Cross-module**: Preparada para relación con `HarvestLot` del módulo `fruit_origin`
- ⚠️ **BLOQUEADO**: Faltan domain services y repositories para validar invariantes de negocio

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
