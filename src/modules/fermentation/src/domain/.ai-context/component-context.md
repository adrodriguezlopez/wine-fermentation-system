# Component Context: Domain Component (Fermentation Management Module)

> **Parent Context**: See `../module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Defines the core business model, domain entities, enums, and repository interfaces for the Fermentation Management Module. Centralizes business rules, contracts, and invariants that must be respected by all other components.

**Position in module**: Acts as the foundation for the entire module. All other components (Service, Repository, API) depend on the abstractions and rules defined here, but the domain does not depend on any other component.

## Architecture pattern
- **Domain-Driven Design (DDD)**: Entities, value objects, enums, and repository interfaces live here.
- **Dependency Inversion Principle**: All dependencies point inward to the domain.

## Arquitectura específica del componente
- **Entities**: Fermentation, BaseSample, FermentationNote, etc. (en `entities/`)
  - ADR-029: Campos `data_source` e `imported_at` para tracking de origen de datos
- **Enums**: FermentationStatus, SampleType, DataSource (ADR-029), etc. (en `enums/`)
- **Repository Interfaces**: IFermentationRepository, ISampleRepository (en `repositories/`)
  - ADR-029: Métodos `list_by_data_source()` en ambas interfaces
- **No lógica de infraestructura**: Solo contratos, reglas y modelos puros.

## Sample types (STI — single table inheritance on `samples` table)

All sample subclasses extend `BaseSample`. No DB migration needed to add a new type — all rows share the `samples` table, differentiated by `polymorphic_identity`.

| Class | `polymorphic_identity` | `units` | Measures |
|-------|------------------------|---------|----------|
| `SugarSample` | `sugar` | brix | Sugar content |
| `DensitySample` | `density` | specific_gravity | Density |
| `CelsiusTemperatureSample` | `temperature` | °C | Temperature |
| `AceticAcidSample` | `acetic_acid` | g/L | Volatile acidity (acetic acid) |

**Adding a new sample type:**
1. Create `src/domain/entities/samples/<name>_sample.py` extending `BaseSample`
2. Set `polymorphic_identity` in `__mapper_args__` and default `units` in `__init__` (use relative import `.base_sample`)
3. Add enum value to `SampleType` (and update any guard tests that assert on `len(SampleType)`)
4. Add class name to `__all__` in `samples/__init__.py` (no import — prevents SQLAlchemy mapper conflicts in pytest)

**Planned (add when frontend + client ready):**
- `LacticAcidSample` (g/L) — malolactic fermentation monitoring
- `SulfurDioxideSample` (mg/L) — SO₂ preservation monitoring

## Component interfaces
- IFermentationRepository: Contrato para persistencia de fermentaciones - create, get_by_id, update, delete get_fermentation_temperature_range, etc.
- ISampleRepository: Contrato para persistencia de muestras - upsert_sample, get_by_id, get_by_fermentation, delete, soft_delete_sample, check_duplicate_timestamp, etc.

## Business rules enforced
- Invariantes de dominio: Relaciones, restricciones y reglas que deben cumplirse siempre a nivel de entidad.
- Tipos y estados válidos definidos por enums.
- Contratos de acceso a datos desacoplados de la infraestructura.

## Connection with other components
- **Service Component**: Usa entidades y contratos para implementar lógica de negocio.
- **Repository Component**: Implementa las interfaces de repositorio para acceso a datos.
- **API Component**: Puede usar entidades para validación o mapeo, pero nunca debe modificar el dominio.

## Implementation status
- **Implemented**: Entidades, enums y contratos principales presentes.
- **Next steps**: Extender reglas de negocio y contratos según necesidades del dominio.

## Key implementation considerations
- El dominio nunca debe depender de infraestructura ni frameworks externos.
- Todas las reglas críticas deben estar aquí para garantizar la integridad del sistema.
- Facilita testing y evolución del modelo de negocio.
