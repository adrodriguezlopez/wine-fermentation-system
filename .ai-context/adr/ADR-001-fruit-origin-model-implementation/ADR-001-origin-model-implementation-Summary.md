Fruit Origin Subdomain Implementation Summary

## Phase 1 Completed ✅
### Subdomain Structure:
Created a new fruit_origin subdomain with an entities folder for DDD consistency.

### Entities Implemented:

**Vineyard**: References winery_id, has unique code per winery, and a list of VineyardBlocks.
**VineyardBlock**: References vineyard_id, has unique code per vineyard, and fields for soil, slope, aspect, area, elevation, latitude, longitude, irrigation, organic certification, and notes. Linked to multiple HarvestLots.
**HarvestLot**: References both winery_id and block_id, has unique code per winery, and fields for harvest date, weight, brix, grape variety, clone, rootstock, pick method, pick times, bins count, field temperature, and notes.

### Relationships:
- Vineyard → VineyardBlock (1:N)
- VineyardBlock → HarvestLot (1:N)
- All entities reference their parent via foreign keys.

## Phase 2 Completed ✅ - Fermentation Entity Update

### Fermentation Entity Refactoring:
**Fields Added:**
- `winery_id: FK → Winery.id` - Replaces string winery field, enables multi-tenant
- `vessel_code: str | None` - Optional vessel identifier with UNIQUE constraint per winery

**Fields Renamed:**
- `initial_fruit_quantity` → `input_mass_kg` - Clearer naming for mass balance validation

**Fields Removed:**
- `winery: str` - Eliminated duplication, use winery_id FK instead
- `vineyard: str` - Eliminated duplication, derived from HarvestLot relationships
- `grape_variety: str` - Eliminated duplication, derived from HarvestLot.grape_variety

### Design Decisions & Trade-offs:

**✅ Benefits:**
- **No data duplication**: Eliminated inconsistencies between Fermentation and HarvestLot data
- **Blend support**: Multiple grape varieties naturally supported via multiple HarvestLots
- **Traceability**: All origin data derives from HarvestLot → VineyardBlock → Vineyard chain
- **Multi-tenant ready**: winery_id prepares for multi-winery scenarios

**⚠️ Trade-offs:**
- **Complex queries**: Displaying grape_variety now requires JOINs with HarvestLot
- **UI considerations**: If UI needs early grape_variety display, use calculated/non-persisted field
- **MVP overhead**: winery_id seems redundant in single-winery MVP but enables business rules

### SQLAlchemy 2.0 Style:
- All models use Mapped[] and mapped_column
- Relationships are type-annotated and use relationship()
- TYPE_CHECKING imports for circular reference handling

### Constraints:
- Unique constraints for codes per context (to be enforced in migrations)
- UNIQUE (winery_id, vessel_code) constraint for vessel identification
- All required and nullable fields as per MVP matrix
- Table and column names use snake_case and plural nouns

### Next Steps:
- Phase 3: ✅ **COMPLETADO** - Implement FermentationLotSource association entity
- Phase 4: 🔄 **EN PROGRESO** - Add Winery entity and complete relationships  
- Phase 5: ⚠️ **BLOQUEADO** - Domain services y repositories (prerequisito crítico)
- Phase 6: ⚠️ **BLOQUEADO** - Database migrations y constraints (depende de Phase 5)
- Phase 7: ⚠️ **BLOQUEADO** - Business logic validation (depende de Phase 5)

### Integration Status:
✅ **Entities**: Ready for domain layer integration  
� **BLOQUEADOR**: Repository y service layer NO implementados  
🔄 **API/DTO layer**: Updates needed for removed fields  
⚠️ **Migration scripts**: Needed for database schema changes (esperando services)

## Phase 3 Completado ✅ - FermentationLotSource Association

### FermentationLotSource Entity Implementada:
**Ubicación**: `src/modules/fermentation/src/domain/entities/fermentation_lot_source.py`

**Campos Obligatorios:**
- `fermentation_id: int` - FK → Fermentation.id
- `harvest_lot_id: int` - FK → HarvestLot.id (fruit_origin module)
- `mass_used_kg: float` - Masa específica usada de este lot

**Campos Opcionales:**
- `notes: str | None` - Notas contextuales para este uso específico

**Constraints SQL implementados:**
- `UNIQUE(fermentation_id, harvest_lot_id)` - No duplicar lot por fermentación
- `CHECK(mass_used_kg > 0)` - Masa debe ser positiva
- `INDEX(fermentation_id)` - Performance para queries de detalle
- `INDEX(harvest_lot_id)` - Performance para historial de uso de lots

### Decisiones de Diseño DDD:
**✅ Razonamiento de Ubicación:**
- Ubicada en módulo `fermentation` porque pertenece al agregado `Fermentation`
- Su ciclo de vida depende de la fermentación (create/update/delete en misma UoW)
- Evita cruzar límites del subdominio `fruit_origin` que posee `HarvestLot`
- Los servicios que manipulan blends viven en fermentation, consultando HarvestLot vía puerto read-only

**✅ Invariantes de Negocio (NO en DB constraints):**
- Balance de masas: Σ mass_used_kg = fermentation.input_mass_kg
- Misma bodega: HarvestLot.winery_id = Fermentation.winery_id
- Fechas coherentes: HarvestLot.harvest_date ≤ Fermentation.start_date

### Testing Status:
- Tests de metadata y estructura: ✅ 5/5 passing
- Tests de lógica de blends y validación: ✅ implementados (lógica básica)
- Relaciones bidireccionales: ✅ definidas en código
  - `Fermentation.lot_sources` → `List[FermentationLotSource]` con cascade="all, delete-orphan"
  - `FermentationLotSource.fermentation` → `Fermentation` con back_populates
  - Relación con `HarvestLot` preparada para integración cross-module
- **⚠️ LIMITACIÓN**: Tests solo validan estructura, no lógica de negocio compleja (requiere services)

## 🚫 DEPENDENCIAS BLOQUEADORAS - Requiere Decisión Arquitectural

### Problema Identificado:
La implementación de ADR-001 requiere **domain services y repositories** que aún no existen en el proyecto:

**Servicios Necesarios:**
- `FermentationBlendService` - Validar balance de masas y composición de blends
- `FruitOriginValidationService` - Validar fechas, misma bodega, etc.
- `HarvestLotRepository` - CRUD para lots del módulo fruit_origin
- `WineryRepository` - CRUD para bodegas (cross-module)

**Invariantes Sin Implementar:**
- Balance de masas: `Σ mass_used_kg = fermentation.input_mass_kg`
- Misma bodega: `HarvestLot.winery_id = Fermentation.winery_id`
- Fechas coherentes: `HarvestLot.harvest_date ≤ Fermentation.start_date`

### Opciones de Continuidad:
1. **PAUSA ADR-001** hasta implementar architecture base (services/repositories)
2. **IMPLEMENTAR arquitectura base** primero, después continuar ADR-001
3. **IMPLEMENTAR solo entities** y dejar business rules para después

### Recomendación:
**OPCIÓN 1: PAUSA** - Mejor tener base sólida de arquitectura antes de continuar con features avanzadas.