---
name: wine-backend-dev
description: >
  Expert backend development skill for the Wine Fermentation System. USE THIS SKILL whenever
  the user wants to add a feature, create a new entity, write a service, implement a repository,
  add an API endpoint, write tests, run migrations, fix a bug, refactor a module, or do anything
  that touches the Python backend. Also use it when the user asks about architecture, TDD workflow,
  module structure, or how to implement something that fits into this codebase. If the user mentions
  fermentation, winery, analysis engine, protocols, samples, fruit origin, or any backend concept —
  this skill applies. Don't wait for an explicit "backend skill" request.
---

# Wine Fermentation System — Backend Development Skill

This system is a **Python microservices backend** for winemaker fermentation monitoring. It uses
Clean Architecture + TDD strictly. Every implementation decision must respect both.

---

## Context hierarchy — read before acting

The `.ai-context/` system is hierarchical. Before starting any task, read context top-down.
A wrong assumption at a higher level corrupts every lower-level decision.

```
NIVEL 1 — Sistema (system-wide rules, tech stack, cross-cutting concerns)
  /.ai-context/project-context.md
  /.ai-context/ARCHITECTURAL_GUIDELINES.md
  /.ai-context/collaboration-principles.md

NIVEL 2 — Módulo (module scope, interfaces, business rules, implementation status)
  src/modules/<module>/.ai-context/module-context.md

NIVEL 3 — Componente (entity detail, validation rules, domain model)
  src/modules/<module>/.ai-context/domain-model-guide.md
  src/modules/<module>/.ai-context/fermentation-validation-catalog.md  (fermentation only)
  src/modules/<module>/.ai-context/protocol/  (protocol component, fermentation only)

NIVEL 4 — Implementación (the actual code)
  src/modules/<module>/src/...
```

**Reading order for a new task:**
1. Read NIVEL 1 files if you don't have system context yet
2. Read the relevant module's `module-context.md` (NIVEL 2) to understand current state and implementation status
3. Read `domain-model-guide.md` (NIVEL 3) if the task involves entities or business rules
4. Read the actual code (NIVEL 4) only for the specific files you'll change

**Quote what you find.** After reading each context file, briefly state what it told you
before proceeding. This prevents acting on assumptions instead of actual state.
Example: "module-context.md shows service layer is complete (728 tests) but API layer is
marked 📋 Planned — so the task is to add the router, not to redo the service."

**When the context is missing** (new module or new component with no `.ai-context/` yet):  
Create it first using the templates in `references/context-templates.md` before writing any code.

The NIVEL 1 context also defines your **feedback mode**: this developer expects critical,
constructive pushback — not agreement. See `/.ai-context/collaboration-principles.md`.

---

## Quick orientation

| Module | Port | Domain |
|--------|------|--------|
| `fermentation` | 8000 | Core fermentation tracking, samples, protocol engine |
| `winery` | 8001 | Multi-tenant organization management |
| `fruit_origin` | 8002 | Vineyard + harvest lot traceability |
| `analysis_engine` | 8003 | Anomaly detection + recommendations |

All modules share one PostgreSQL database (via dockerized `db` service) and import from
`src/shared/` for cross-cutting concerns (auth, ORM base, logging, error handlers).

---

## Architecture rules (enforce strictly)

### Layer order — never invert dependencies

```
domain/          ← entities, DTOs, enums, repository INTERFACES (no framework deps)
repository_component/  ← SQLAlchemy implementations of domain interfaces
service_component/     ← business logic; depends on domain interfaces, not implementations
api/ or api_component/ ← FastAPI routers + schemas (DTOs for HTTP); calls services
```

Domain layer has zero knowledge of SQLAlchemy, FastAPI, or any infrastructure detail.
Services receive repository **interfaces** via dependency injection — never concrete classes.

### Naming conventions by module

The fermentation module uses `api/`, `repository_component/`, `service_component/`.
Winery and fruit_origin use `api_component/`, `repository_component/`, `service_component/`.
Analysis engine uses `api/`, `repository_component/`, `service_component/`.
Match the existing convention of the module you're working in.

### Import rule — absolute paths only

Always use absolute imports from the workspace root. The CI enforces this:

```python
# ✅ Correct
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.shared.infra.orm.base_entity import BaseEntity
from src.shared.auth.domain.entities.user import User

# ❌ Wrong — will fail CI
from domain.entities.fermentation import Fermentation
from shared.infra.orm.base_entity import BaseEntity
```

### Multi-tenancy — mandatory on all domain entities

Every entity that belongs to a winery must carry `winery_id`. Services must scope all
queries by `winery_id` to enforce per-winery data isolation. Never return data across
winery boundaries. Raise `CrossWineryAccessDenied` (from `src.shared.domain.errors`) if violated.

### BaseEntity — always extend it

```python
from src.shared.infra.orm.base_entity import BaseEntity

class MyEntity(BaseEntity):
    __tablename__ = "my_entities"
    # BaseEntity provides: id, created_at, updated_at, is_deleted, winery_id
```

---

## TDD workflow — Red → Green → Refactor

This codebase is developed test-first. Follow this order for every feature:

### Step 0 — Create a feature branch

Before writing any code, create a branch from `main` (or the current base branch):

```powershell
git checkout main
git pull
git checkout -b feat/<short-feature-name>
```

Branch naming:
- `feat/<name>` — new feature or entity
- `fix/<name>` — bug fix
- `refactor/<name>` — refactor with no behavior change

**Never implement directly on `main`.** If already on `main` with uncommitted changes, create the branch first (`git checkout -b feat/<name>`) — your uncommitted changes carry over.

Skip this step only for trivial single-file fixes that the user explicitly says don't need a branch.

### Step 1 — Write the failing test first

Before writing any implementation code, write the test that describes the desired behavior.
Tests live inside the module: `src/modules/<module>/tests/unit/` or `tests/integration/`.

Structure tests by domain concept, not by file:
```
tests/unit/
├── fermentation_lifecycle/   # service-level behavior
├── repository_component/     # repository tests (mocked session)
├── api/                      # API endpoint tests
└── domain/                   # entity/value object tests
```

### Step 2 — Run the test, confirm it fails

```powershell
cd src/modules/<module>
poetry run pytest tests/unit/path/to/test_file.py -v
```

### Step 3 — Implement the minimum code to make it pass

Write only what the test requires. No gold-plating.

### Step 4 — Run all tests, confirm nothing regressed

```powershell
poetry run pytest --cov=src --cov-report=term-missing
```

### Step 5 — Update `.ai-context/` — mandatory, not optional

Do this before calling the task done. Update every file that reflects what changed:

- **New entity or service added** → update `module-context.md` component list
- **Test count changed** → update `module-context.md` AND `project-context.md` test counts
- **New module** → update `PROJECT_STRUCTURE_MAP.md` and `project-context.md`
- **Domain model changed** → update `domain-model-guide.md`

Stale context causes wrong assumptions in the next session. Updating it is part of the implementation, not cleanup.

See the **Context maintenance** section at the bottom of this skill for the full checklist.

### Step 6 — Run the full test suite for ALL modules

After any change, run the complete suite from the workspace root to confirm nothing regressed across modules:

```powershell
python run_all_tests.ps1
```

Or per-module if you only changed one:

```powershell
cd src/modules/<module>
poetry run pytest --cov=src --cov-report=term-missing
```

**Do not consider the task complete until all tests pass.** If a test that was passing before now fails, fix it before finishing — don't leave regressions for the next session.

---

## Test patterns

### Unit test for a service (mock the repository interface)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.domain.interfaces.fermentation_repository_interface import IFermentationRepository

@pytest.fixture
def mock_repo():
    return AsyncMock(spec=IFermentationRepository)

@pytest.fixture
def service(mock_repo):
    return FermentationService(repository=mock_repo)

@pytest.mark.asyncio
async def test_create_fermentation_sets_active_status(service, mock_repo):
    mock_repo.create.return_value = MagicMock(id=1, status="ACTIVE")
    result = await service.create(winery_id=1, ...)
    assert result.status == "ACTIVE"
    mock_repo.create.assert_called_once()
```

### Unit test for a repository (mock the DB session)

```python
@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_get_by_id_returns_entity(mock_session):
    repo = FermentationRepository(session=mock_session)
    mock_session.execute.return_value.scalars.return_value.first.return_value = fake_entity
    result = await repo.get_by_id(id=1, winery_id=1)
    assert result.id == 1
```

### conftest.py — every module test folder must have one

```python
import sys
from pathlib import Path
import pytest

workspace_root = Path(__file__).parent.parent.parent.parent.parent  # adjust depth
sys.path.insert(0, str(workspace_root))

@pytest.fixture(scope="function")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```

---

## Scenario: creating a brand new module

When the user asks what to do **before writing code** for a new module, your answer is
**exclusively the setup phase** — do not write entity, service, or API code. The setup phase
is complete when all context and config files exist. Implementation is a separate task.

**SETUP PHASE ONLY — output nothing else when asked "what to do before writing code":**

1. Create `src/modules/<name>/.ai-context/module-context.md` — use **Template 1** in `references/context-templates.md`
2. Create `src/modules/<name>/.ai-context/domain-model-guide.md` — use **Template 2**
3. Add module entry to `/.ai-context/project-context.md` — use **Template 4** (status: 📋 Planned, tests: 0)
4. Add module entry to `/.ai-context/PROJECT_STRUCTURE_MAP.md` — use **Template 6** (all icons 📋)
5. Add governing ADR to `/.ai-context/adr/ADR-INDEX.md` if one exists — use **Template 5**
6. Create `src/modules/<name>/pyproject.toml` (copy from nearest module, adjust name/port)
7. Create `src/modules/<name>/Dockerfile` (copy from nearest module, adjust module name)
8. Create `src/modules/<name>/README.md` (one paragraph describing the module)
9. Create `src/modules/<name>/tests/conftest.py` (sys.path setup + event_loop fixture — see TDD section)
10. Add service block to `docker-compose.yml` (pick next available port, copy pattern from existing service)

After outputting these files, **stop**. Tell the user: "Context and config are ready. Ask me to
start on the domain entities when you're ready to write code."

> File templates for steps 1–5: `references/context-templates.md`

---

## Scenario: adding a new component to an existing module

A "component" is a cohesive group of entities + repository + service + API (e.g., adding the
Protocol Engine to the Fermentation module). Do this before writing implementation:

1. Add a new component block to the module's `module-context.md` — use **Template 3** in `references/context-templates.md`
2. Add new entity/enum entries to `domain-model-guide.md`
3. If this is ADR-driven, add to `ADR-INDEX.md` — use **Template 5**

Mark the block `📋 Planned` when added, `🔄 In Progress` when work starts,
`✅ COMPLETE` when all tests pass. Then move it under `### Completed Components`.

---

## Adding a new entity — checklist

1. **Domain entity** in `src/domain/entities/my_entity.py` — extends `BaseEntity`, includes `winery_id`
2. **Enum(s)** in `src/domain/enums/` if the entity has status/type fields
3. **DTOs** in `src/domain/dtos/` for create/update/response shapes (Pydantic v2)
4. **Repository interface** in `src/domain/interfaces/` (Protocol class, async methods)
5. **Repository implementation** in `src/repository_component/` (extends `BaseRepository`)
6. **Service interface** in `src/service_component/interfaces/`
7. **Service implementation** in `src/service_component/services/`
8. **API router** in `src/api/routers/` or `src/api_component/routers/`
9. **Register router** in the module's `main.py` / `app.py`
10. **Alembic migration** — always create one, never hand-edit tables
11. **Tests** — unit tests for service + repository, integration test for the endpoint
12. **Update `.ai-context/module-context.md`** with new component + test count

---

## Running the stack

```powershell
# Start all services
docker-compose up --build

# Run migrations only
docker-compose run --rm migrate

# Run a specific module's tests (independent poetry env)
cd src/modules/fermentation
poetry run pytest -v

# Run all tests from workspace root
python run_all_tests.ps1

# Lint checks — ALL must pass **locally before pushing** (not just before committing)
poetry run black . --check
poetry run flake8 .
poetry run mypy src
```

---

## Type annotation standards — enforce strictly on new code

This codebase targets `mypy strict = true`. There is existing type debt in 17 files
(tracked in GitHub issue #3) that is temporarily silenced with `ignore_errors = true`
overrides. **Do not add new overrides.** Fix errors instead.

**Every new function, method, and class you write must be fully typed:**

```python
# ✅ Correct — full annotations
async def create_fermentation(
    self,
    winery_id: int,
    data: FermentationCreateDTO,
) -> Fermentation:
    ...

# ❌ Wrong — missing annotations (mypy strict will reject this)
async def create_fermentation(self, winery_id, data):
    ...
```

**Rules:**
- All function arguments and return types must be annotated
- Use `list[X]` not `List[X]` (Python 3.9+)
- Use `dict[K, V]` not `Dict[K, V]`
- Use `X | None` not `Optional[X]` (or `Optional` when on Python <3.10 — use `from __future__ import annotations`)
- Never use bare `Any` — if you must, add a `# type: ignore[assignment]` with a comment explaining why
- SQLAlchemy scalars return `Sequence[T]` — cast to `list` when your return type is `list[T]`: `return list(result.scalars().all())`
- For `TYPE_CHECKING` guards: use `from __future__ import annotations` + `if TYPE_CHECKING:` block for forward references

**Before pushing any backend code, run and confirm all three pass:**

```powershell
poetry run black . --check   # formatting
poetry run flake8 .          # style + unused imports
poetry run mypy src          # type checking — zero errors expected on new code
```

---

## Alembic migrations

Migrations live in `alembic/versions/`. Always create a new revision — never modify existing ones.

```powershell
# Generate a new migration
alembic revision --autogenerate -m "description_of_change"

# Apply migrations
alembic upgrade head

# Check current state
alembic current
```

Naming pattern: `NNN_short_description.py` (e.g., `008_add_harvest_lot_notes.py`).

---

## Shared infrastructure — what lives where

| Need | Import from |
|------|-------------|
| Base ORM entity | `src.shared.infra.orm.base_entity.BaseEntity` |
| DB session (FastAPI DI) | `src.shared.infra.database.fastapi_session` |
| Auth / user context | `src.shared.auth.domain.entities.user.User` |
| Structured logging | `src.shared.wine_fermentator_logging` |
| Error base classes | `src.shared.domain.errors` |
| RFC 7807 error handlers | `src.shared.api.error_handlers` |

---

## SOLID checklist — review before submitting

- **SRP**: Does each class have exactly one reason to change?
- **OCP**: Can the behavior be extended without modifying existing code?
- **LSP**: Can any implementation be swapped for another behind the same interface?
- **ISP**: Are interfaces small and specific (not one fat interface per module)?
- **DIP**: Do services and routers depend on interfaces, not concrete classes?

If the answer is no on any of these, push back and propose the correct design.

---

## Context maintenance — developer responsibility

> Full checklist: see `references/context-maintenance.md` in this skill folder.
> File templates (for creating new context files): see `references/context-templates.md`

The `.ai-context/` files are living documentation. Update them when:

| Change | What to update |
|--------|---------------|
| New entity added | `module-context.md` (add to component list), `PROJECT_STRUCTURE_MAP.md` |
| Test count changes | `project-context.md` (module test counts), `module-context.md` |
| New ADR created | `adr/ADR-INDEX.md`, link from relevant `module-context.md` |
| Domain model changes | `domain-model-guide.md` in the module's `.ai-context/` |
| New validation rule | `fermentation-validation-catalog.md` (if fermentation module) |
| New module created | `project-context.md` (module list), `PROJECT_STRUCTURE_MAP.md` |
| Architecture decision changed | Create new ADR, update `ARCHITECTURAL_GUIDELINES.md` if it's a system-wide rule |

Files to keep current:
- `/.ai-context/project-context.md` — system-level status + test counts
- `/.ai-context/PROJECT_STRUCTURE_MAP.md` — navigation map
- `src/modules/<module>/.ai-context/module-context.md` — per-module status
- `/.ai-context/adr/ADR-INDEX.md` — ADR list

**Rule**: If you implement something and don't update context, the next developer (or AI session)
will have stale information. Stale context causes wrong assumptions and wasted work.

---

## Feedback mode

This project follows explicit critical-feedback principles (see `/.ai-context/collaboration-principles.md`).
Do not just agree with decisions. If a proposed design violates SOLID, introduces tight coupling,
makes testing harder, or has a better alternative — say so clearly with a concrete alternative.
