# Implementing `FermentationNote` End-to-End

## What I read before answering

**NIVEL 1 — `project-context.md`**: System is a Python microservices backend (Clean Architecture + TDD). 1,390 tests passing. Multi-tenant: every entity scoped by `winery_id`. Absolute imports are mandatory.

**NIVEL 2 — `fermentation/module-context.md`**: Module is fully complete — Domain, Repository, Service, and API layers all exist. Specifically: `FermentationNoteRepository` is listed as complete with 19 unit tests and 20 integration tests. The module uses `api/`, `repository_component/`, `service_component/` naming (not `api_component/`). ~700 tests passing.

**NIVEL 3 — `domain-model-guide.md`**: `FermentationNote` is already in the ubiquitous language glossary: *"Observation or action taken during the process, associated with a fermentation."* It belongs to a `Fermentation` and a `User`.

**NIVEL 4 — Actual code**: I read all the relevant files.

---

## Honest assessment before we start

Good news and a caution.

**The good news**: The `FermentationNote` entity is substantially further along than you might think. Here's what already exists:

| Layer | File | Status |
|-------|------|--------|
| Domain entity | `src/domain/entities/fermentation_note.py` | ✅ Exists |
| Domain DTOs | `src/domain/dtos/fermentation_note_dtos.py` | ✅ Exists (`FermentationNoteCreate`, `FermentationNoteUpdate`) |
| Repository interface | `src/domain/repositories/fermentation_note_repository_interface.py` | ✅ Exists (`IFermentationNoteRepository`) |
| Repository implementation | `src/repository_component/repositories/fermentation_note_repository.py` | ✅ Exists (5 methods: create, get_by_id, get_by_fermentation, update, delete) |
| DB migration | `alembic/versions/000_baseline_schema.py` | ✅ Table `fermentation_notes` in baseline schema |
| Unit tests (repo) | `tests/unit/repository_component/test_fermentation_note_repository.py` | ✅ 19 tests |
| Integration tests (repo) | `tests/integration/repository_component/test_fermentation_note_repository_integration.py` | ✅ 20 tests |

**The caution — two things are genuinely missing:**

1. **No service layer** for `FermentationNote`. There is no `FermentationNoteService` or `IFermentationNoteService`. The existing `FermentationService` and `SampleService` don't cover notes. This is the most important gap.
2. **No API router** for notes. There is no `note_router.py`, no note request/response schemas, and no note dependency in `dependencies.py`. The notes are unreachable via HTTP.

Before writing a single line of code, read the existing files. Don't repeat work — build on what's there.

---

## Step 0 — Read before touching anything

```
# In this order:
src/modules/fermentation/src/domain/entities/fermentation_note.py
src/modules/fermentation/src/domain/dtos/fermentation_note_dtos.py
src/modules/fermentation/src/domain/repositories/fermentation_note_repository_interface.py
src/modules/fermentation/src/repository_component/repositories/fermentation_note_repository.py
tests/unit/repository_component/test_fermentation_note_repository.py
tests/integration/repository_component/test_fermentation_note_repository_integration.py
src/modules/fermentation/src/service_component/services/fermentation_service.py  # pattern reference
src/modules/fermentation/src/api/routers/sample_router.py                        # pattern reference
src/modules/fermentation/src/api/dependencies.py                                  # wire-up reference
```

Two specific things to note when reading the entity:

1. **`winery_id` is absent from `FermentationNote` directly** — the entity doesn't have its own `winery_id` column. Multi-tenancy is enforced by JOINing through the parent `Fermentation`. This is the correct design here (notes are owned by their fermentation, which owns `winery_id`). The repository already handles this correctly in all 5 methods.
2. **`BaseEntity` does not include `winery_id`** in this codebase (confirmed from the shared code). The `SKILL.md` says BaseEntity provides `winery_id` — that's aspirational documentation, not the current reality. Do not add a `winery_id` column to `FermentationNote`. The JOIN pattern is correct and consistent with how the repo was built.

---

## Step 1 — Service interface (TDD: write the test first)

**What to create**: `src/modules/fermentation/src/service_component/interfaces/fermentation_note_service_interface.py`

The service interface defines the contract. Look at `IFermentationService` and `ISampleService` for the pattern — `Protocol` or `ABC`, async methods, typed with domain DTOs, not ORM entities in the signature.

The interface needs these methods (infer from the repository surface area and what a winemaker would do):

- `add_note(fermentation_id, winery_id, note_text, action_taken, user_id) -> FermentationNote`
- `get_note(note_id, winery_id) -> FermentationNote`
- `list_notes(fermentation_id, winery_id) -> List[FermentationNote]`
- `update_note(note_id, winery_id, note_text?, action_taken?) -> FermentationNote`
- `delete_note(note_id, winery_id) -> None`

**Before writing the interface**, write the test file first:

```
tests/unit/fermentation_lifecycle/test_fermentation_note_service.py
```

In that test file, you'll mock `IFermentationNoteRepository` using `AsyncMock(spec=IFermentationNoteRepository)` and inject it into the service constructor. Look at `tests/unit/fermentation_lifecycle/` for the existing service test pattern — you'll see the `AsyncMock(spec=...)` injection pattern and how `pytest.mark.asyncio` is used.

**What to test (not how — that's your job):**
- `add_note` — happy path creates note via repo, returns entity
- `add_note` — if fermentation not found (repo raises `EntityNotFoundError`), service re-raises as `NotFoundError`
- `get_note` — happy path returns entity
- `get_note` — not found raises `NotFoundError`
- `list_notes` — returns list (can be empty)
- `update_note` — happy path, partial update supported
- `update_note` — not found raises `NotFoundError`
- `delete_note` — happy path
- `delete_note` — not found raises `NotFoundError`

Run the test, confirm it fails (the service doesn't exist yet):

```powershell
cd src/modules/fermentation
poetry run pytest tests/unit/fermentation_lifecycle/test_fermentation_note_service.py -v
```

---

## Step 2 — Service implementation

**What to create**: `src/modules/fermentation/src/service_component/services/fermentation_note_service.py`

Write only enough to make the failing tests pass.

Key design decisions to enforce:
- Constructor receives `IFermentationNoteRepository` (the interface, not the concrete class — DIP)
- The service translates `EntityNotFoundError` (repository layer) to `NotFoundError` (service layer). Don't leak infrastructure errors up through the API
- Do **not** add business rules that aren't tested. `FermentationNote` is free-text — there's no glucose/ethanol-style validation here
- Import style (absolute, mandatory):
  ```python
  from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import IFermentationNoteRepository
  from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import FermentationNoteCreate, FermentationNoteUpdate
  from src.modules.fermentation.src.service_component.errors import NotFoundError
  ```

Run the test again after implementation, confirm green:

```powershell
poetry run pytest tests/unit/fermentation_lifecycle/test_fermentation_note_service.py -v
```

Then run the full suite to confirm no regressions:

```powershell
poetry run pytest tests/ --cov=src --cov-report=term-missing
```

---

## Step 3 — API schemas (request + response)

**What to create**:
- `src/modules/fermentation/src/api/schemas/requests/note_requests.py`
- `src/modules/fermentation/src/api/schemas/responses/note_responses.py`

Look at `sample_requests.py` and `sample_responses.py` for the Pydantic v2 pattern.

**Request schema** (`NoteCreateRequest`): 
- `note_text: str` — required, non-empty
- `action_taken: str` — required, max 255 chars
- No `created_by_user_id` here — that comes from the JWT context (`current_user.id`), never from the request body. This is a security requirement, not a style choice.

**Update schema** (`NoteUpdateRequest`):
- `note_text: Optional[str] = None`
- `action_taken: Optional[str] = None`
- Add a model validator: raise `ValueError` if both are `None` (a no-op update)

**Response schema** (`NoteResponse`):
- `id: int`
- `fermentation_id: int`
- `note_text: str`
- `action_taken: str`
- `created_by_user_id: int`
- `created_at: datetime`
- `updated_at: datetime`

Use `model_config = ConfigDict(from_attributes=True)` so the response can be constructed directly from the ORM entity.

---

## Step 4 — API router (TDD: write the test first)

**What to create**: `tests/unit/api/test_note_router.py` (or `tests/api/` — match the existing structure)

Check `tests/unit/api/` and `tests/api/` to see where the existing API tests live and how they're structured. They use `AsyncClient` from `httpx` with the FastAPI app. Look at the sample router tests as your closest pattern.

**What to test (not how):**
- `POST /fermentations/{id}/notes` — 201, returns created note
- `POST /fermentations/{id}/notes` — 404 if fermentation not found
- `POST /fermentations/{id}/notes` — 401 if no auth
- `GET /fermentations/{id}/notes` — 200, returns list
- `GET /fermentations/{id}/notes/{note_id}` — 200, returns single note
- `GET /fermentations/{id}/notes/{note_id}` — 404 if not found
- `PATCH /fermentations/{id}/notes/{note_id}` — 200 on success
- `DELETE /fermentations/{id}/notes/{note_id}` — 204 on success

Confirm the tests fail before writing the router.

**What to create**: `src/modules/fermentation/src/api/routers/note_router.py`

Endpoint design — nest under fermentations (same pattern as samples):

```
POST   /fermentations/{fermentation_id}/notes           → add note
GET    /fermentations/{fermentation_id}/notes           → list notes
GET    /fermentations/{fermentation_id}/notes/{note_id} → get note
PATCH  /fermentations/{fermentation_id}/notes/{note_id} → update note
DELETE /fermentations/{fermentation_id}/notes/{note_id} → delete note (204)
```

Key implementation rules:
- Use `require_winemaker` from `src.shared.auth.infra.api.dependencies` — notes are winemaker-only operations
- Extract `winery_id` and `user.id` from `current_user: UserContext` (from `require_winemaker`)
- Use `@handle_service_errors` from `src.modules.fermentation.src.api.error_handlers` — this is what maps `NotFoundError → 404` without try/except boilerplate in every endpoint
- Inject the service via `Depends(get_fermentation_note_service)` — do not instantiate repositories directly in the router

---

## Step 5 — Wire up the dependency injection

**File to edit**: `src/modules/fermentation/src/api/dependencies.py`

Add two functions (follow the existing pattern for `get_fermentation_repository` / `get_fermentation_service`):

```python
async def get_fermentation_note_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> IFermentationNoteRepository:
    session_manager = FastAPISessionManager(session)
    return FermentationNoteRepository(session_manager)


async def get_fermentation_note_service(
    note_repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)]
) -> IFermentationNoteService:
    return FermentationNoteService(note_repo=note_repo)
```

Absolute imports (mandatory):
```python
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import IFermentationNoteRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import FermentationNoteRepository
from src.modules.fermentation.src.service_component.interfaces.fermentation_note_service_interface import IFermentationNoteService
from src.modules.fermentation.src.service_component.services.fermentation_note_service import FermentationNoteService
```

---

## Step 6 — Register the router

**File to edit**: Find the module's `main.py` or `app.py` (check `src/modules/fermentation/`).

Look at how `sample_router` is registered — copy that pattern exactly. The note router uses the same prefix scheme (`/fermentations`), so the tag should be `"fermentation-notes"` to distinguish it in Swagger.

---

## Step 7 — Alembic migration

The `fermentation_notes` table already exists in the baseline schema (`000_baseline_schema.py`). **Do not create a new migration for the table itself.** It's there.

You only need a migration if you're adding a column. Based on the entity definition I read, the entity has: `fermentation_id`, `created_by_user_id`, `note_text`, `action_taken`, `is_deleted`, plus `id`, `created_at`, `updated_at` from the base. That matches a full note entity.

Check the current schema to confirm:

```powershell
alembic current
```

If you added any new column that doesn't exist in the baseline, then:

```powershell
alembic revision --autogenerate -m "add_<column>_to_fermentation_notes"
alembic upgrade head
```

Use naming pattern `008_add_<something>_to_fermentation_notes.py` (next number after `007_create_winemaker_actions.py`).

If the table definition matches perfectly — no migration needed.

---

## Step 8 — Run the full test suite

```powershell
cd src/modules/fermentation
poetry run pytest tests/ -v
```

Target: all existing ~700 tests still pass, plus your new service and API tests.

From workspace root:
```powershell
.\run_all_tests.ps1
```

Target: ~1,390 + your new tests.

---

## Step 9 — Update `.ai-context/`

The skill requires this before you call the work done. Update:

1. **`module-context.md`** — the service layer section lists services without a `FermentationNoteService`. Add it. Update the test count.
2. **`module-context.md`** — the API layer section lists routers without a notes router. Add it with endpoint list.
3. **`project-context.md`** — update the fermentation test count from 728 to your new total.
4. **`domain-model-guide.md`** — `FermentationNote` is already in the glossary and entity map. No change needed unless you added fields.

---

## SOLID check — before you submit

Review each decision against the checklist:

| Principle | Check |
|-----------|-------|
| SRP | `FermentationNoteService` handles only note operations. Does not touch fermentation status or sample validation. ✅ |
| OCP | Adding notes didn't modify `FermentationService` or `SampleService`. ✅ |
| LSP | `FermentationNoteService` satisfies `IFermentationNoteService` — any implementation can replace it behind the interface. Verify this by running with the mock in tests. |
| ISP | `IFermentationNoteService` is a focused interface for note operations only — not a fat "everything" interface. ✅ |
| DIP | Router depends on `IFermentationNoteService` (interface). Service depends on `IFermentationNoteRepository` (interface). Neither depends on concrete classes. Verify in your constructor signatures. |

---

## One design decision to flag upfront

The existing `FermentationNoteCreate` DTO requires `action_taken` as a **required** field. That means every note must include both `note_text` (the free-text observation) and `action_taken` (what was done). You said the requirement is "free-text note... timestamp and user who wrote it."

**Pushback**: If `action_taken` is truly required at the DTO level, your API `NoteCreateRequest` must include it as required too — or you'll have a mismatch between the HTTP layer and the domain DTO. Don't hide required fields.

If the product intent is that notes are purely free-text observations with no required action field, that's a domain model change — update `FermentationNoteCreate`, `FermentationNoteUpdate`, the entity's column (nullable), and the existing repository tests. That's a separate, deliberate decision. Don't paper over it silently.

Clarify with the team which intent is correct before writing the API layer.
