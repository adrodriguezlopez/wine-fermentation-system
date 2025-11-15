
# Folder Structure for wine-fermentation-system

This document describes the recommended and current folder/file structure for the entire wine-fermentation-system project, following DDD and project conventions. The fruit_origin section is included as a focused example.

---

## Top-Level Structure

```
wine-fermentation-system/
│
├── .ai-context/                  # Architecture, ADRs, and context docs
│   ├── adr/                      # Architecture Decision Records (ADRs)
│   ├── project-context.md        # System-level context
│   ├── module-context.md         # Module-level context
│   └── ...
│
├── src/
│   └── modules/
│       └── fermentation/
│           ├── src/
│           │   ├── domain/
│           │   │   ├── entities/                  # Core domain entities (User, Fermentation, etc.)
│           │   │   ├── fruit_origin/              # Subdomain for fruit origin
│           │   │   │   └── entities/
│           │   │   │       ├── vineyard.py
│           │   │   │       ├── vineyard_block.py
│           │   │   │       ├── harvest_lot.py
│           │   │   │       └── __init__.py
│           │   │   └── ... (other subdomains)
│           │   ├── service_component/             # Business logic and orchestration
│           │   │   ├── services/
│           │   │   ├── interfaces/
│           │   │   ├── models/
│           │   │   │   ├── entities/
│           │   │   │   ├── schemas/
│           │   │   │   └── validations/
│           │   │   └── ...
│           │   ├── repository_component/          # Infrastructure/repository implementations
│           │   │   └── ...
│           │   └── api_component/                 # FastAPI endpoints
│           │       └── ...
│           ├── tests/
│           │   ├── unit/
│           │   ├── integration/
│           │   └── fixtures/
│           └── ... (config, migrations, etc.)
│
├── docker/
├── scripts/
├── requirements.txt / pyproject.toml
├── Dockerfile / docker-compose.yml
└── README.md
```

---

## Example: Full Path for Each fruit_origin Entity

- `src/modules/fermentation/src/domain/fruit_origin/entities/vineyard.py`
- `src/modules/fermentation/src/domain/fruit_origin/entities/vineyard_block.py`
- `src/modules/fermentation/src/domain/fruit_origin/entities/harvest_lot.py`

## Integration Points

- `Winery` entity: referenced via `winery_id` (lives outside fruit_origin)
- `Fermentation` entity: will be updated to reference `winery_id` and link to `FermentationLotSource` (association table)

## Future Extensions

- Add `FermentationLotSource` entity in a similar structure when implementing the association table.
- Add repository, service, and API folders as needed for DDD layering.

---

> **Note:** All table and file names use snake_case and plural nouns for consistency. Adjust as needed for your team's conventions.

---

## ⚠️ IMPORTANT UPDATE (2025-10-05)

**This ADR is now OUTDATED.** The folder structure described above shows `fruit_origin` as a **subdomain within fermentation** module. 

**Current structure (post ADR-004):**
- `fruit_origin` is now a **separate top-level module** under `src/modules/fruit_origin/`
- `winery` is also a **separate top-level module** under `src/modules/winery/`
- `harvest/` module was **eliminated** (was duplicate of fruit_origin)

**See:**
- **ADR-004:** Harvest Module Consolidation & SQLAlchemy Registry Fix - Documents the module consolidation decision
- **PROJECT_STRUCTURE_MAP.md:** Current folder structure with all 7 modules
- **.ai-context/fruit_origin/module-context.md:** fruit_origin as bounded context
- **.ai-context/winery/module-context.md:** winery as bounded context

**Rationale for change:**
- `fruit_origin` and `winery` represent separate **bounded contexts** in DDD
- Dependency direction: `fermentation` → `fruit_origin` → `winery`
- Allows independent evolution of each bounded context
- Cleaner module boundaries and multi-tenancy enforcement

This ADR remains as **historical reference** for initial folder structure thinking. For current structure, refer to PROJECT_STRUCTURE_MAP.md and ADR-004.
