
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
