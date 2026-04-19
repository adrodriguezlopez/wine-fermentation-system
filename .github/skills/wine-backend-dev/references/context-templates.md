# Context File Templates

Use these templates when creating `.ai-context/` files from scratch (new module) or when
adding a new component block to an existing context file.

---

## Template 1 — `module-context.md` (new module)

Create this file at `src/modules/<module_name>/.ai-context/module-context.md`.

```markdown
# Module Context: <Module Display Name>

> **Parent Context**: See `/.ai-context/project-context.md` for system-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Module responsibility

**<One sentence: what domain problem does this module solve>**

**Position in system**: <Where it sits in the data/dependency flow>

## Technology stack

- **Framework**: FastAPI (Python 3.9+) — independent service on port **<PORT>**
- **Database**: PostgreSQL with SQLAlchemy ORM (AsyncSession)
- **Validation**: Pydantic V2 models for request/response handling
- **Testing**: pytest with `unittest.mock.AsyncMock`
- **Dependency management**: Independent **Poetry** virtual environment
- **Logging**: Loguru for structured logging
- **Code Quality**: Black (formatting), flake8 (linting)

## Module interfaces

**Receives from**: <What triggers or calls this module>
**Provides to**: <Who consumes the output>
**Depends on**: <External modules or shared infra this module relies on>

## Key functionality

- **<Feature 1>**: <Brief description>
- **<Feature 2>**: <Brief description>

## Business rules

- **<Rule 1>**: <Description>
- **<Rule 2>**: <Description>

## Module components

### <Component Name> — 📋 Planned | 🔄 In Progress | ✅ COMPLETE

**Purpose**: <What this component does>

**Status**: <X/Y tests PASSING ✅ | or: Not yet implemented>

- **Domain Layer** (`src/domain/`):
  - **Entities**: <List entities>
  - **Enums**: <List enums>
  - **DTOs**: <List DTOs>
  - **Interfaces**: <List repository interfaces>

- **Repository Layer** (`src/repository_component/`):
  - **<RepositoryName>**: <N methods, brief description>

- **Service Layer** (`src/service_component/`):
  - **<ServiceName>**: <N methods, brief description>

- **API Layer** (`src/api/routers/` or `src/api_component/routers/`):
  - **<RouterName>**: <N endpoints, brief description>

- **Alembic Migration**:
  - `<NNN_migration_name.py>`: Creates <tables>

- **Tests**: <N/N PASSING ✅ | Planned: N>

## Implementation status

**Status:** 📋 Planned | 🔄 In Progress | ✅ COMPLETE
**Last Updated:** <YYYY-MM-DD>
**Reference:** <ADR numbers governing this module>

### Completed Components
<!-- Move component sections here once done -->

### Planned Components
<!-- List ADR-driven future work here -->
```

---

## Template 2 — `domain-model-guide.md` (new module)

Create this file at `src/modules/<module_name>/.ai-context/domain-model-guide.md`.

```markdown
# <Module Name> Domain Model Guide

---

## 1. Ubiquitous Language Glossary

| Business Concept | Code / Entity | Technical Definition |
|-----------------|---------------|---------------------|
| <Term> | `<ClassName>` | <What it means in this domain> |

---

## 2. Domain Entities Map

### Main Entities

- **<EntityName>**
  - Responsibility: <Single sentence>
  - Relationships: <How it relates to other entities>
  - States: <status field and its possible values, if any>
  - Rules: <Key business constraints>

#### Relationship Diagram

```mermaid
classDiagram
    <Entity1> --> <Entity2> : relationship
```

---

## 3. Value Objects Catalog

<!-- List value objects if any, or note they are not yet extracted -->

Currently no explicit value objects identified. Candidates:
- `<Concept>` — could encapsulate validation for <field>

---

## 4. Enums Reference

| Enum | Values | Usage |
|------|--------|-------|
| `<EnumName>` | `VALUE1, VALUE2` | <Where it's used> |

---

## 5. Business Rule Summary

| Rule | Entity | Enforcement Point |
|------|--------|------------------|
| <Rule description> | `<Entity>` | Service / Repository / DB constraint |
```

---

## Template 3 — New component block (add to existing `module-context.md`)

When adding a new component (e.g., a new entity + service + API) to an **existing** module,
add this block under `## Module components` in the module's `module-context.md`.

```markdown
### <New Component Name> (ADR-<NNN>) — 📋 Planned

**Purpose**: <What this component adds to the module>

**Status**: Not yet implemented

- **Domain Layer**:
  - Entities: `<EntityName>` — <1-line description>
  - Enums: `<EnumName>` — <values>
  - Interfaces: `I<Name>Repository` — <N planned methods>

- **Repository Layer**: `<Name>Repository` — <N planned methods>

- **Service Layer**: `<Name>Service` — <N planned methods>

- **API Layer**: `<N>` endpoints planned — see ADR-<NNN>

- **Tests**: <N> tests planned (unit + integration)

**Reference**: See [ADR-<NNN>-<slug>.md](../../.ai-context/adr/ADR-<NNN>-<slug>.md)
```

Mark it `🔄 In Progress` when work starts, `✅ COMPLETE` when tests pass, and move it under
`### Completed Components`.

---

## Template 4 — New module entry in `project-context.md`

When a new module is created, add this block under `## System modules` in
`/.ai-context/project-context.md`:

```markdown
### <Module Display Name>
**Status:** 📋 Planned
**Last Updated:** <YYYY-MM-DD>
**Total Tests:** 0 (not yet implemented)
**Details:** See [<module> module-context.md](../src/modules/<module>/.ai-context/module-context.md)
```

---

## Template 5 — New ADR entry in `ADR-INDEX.md`

```markdown
| ADR-<NNN> | <Title> | <Proposed \| Accepted \| Superseded> | <YYYY-MM-DD> | <1-line summary> |
```

---

## Template 6 — New module entry in `PROJECT_STRUCTURE_MAP.md`

Add under `## 📁 Core Structure` → `modules/`:

```markdown
├── <module_name>/                        # <emoji> <Module Display Name>
│   ├── src/
│   │   ├── domain/                       # 📋 Entities, DTOs, Enums, Interfaces
│   │   │   ├── entities/                 # <EntityName>
│   │   │   ├── dtos/                     # <DtoName>
│   │   │   └── enums/                    # <EnumName>
│   │   ├── repository_component/         # 📋 Repository implementations
│   │   ├── service_component/            # 📋 Service layer
│   │   └── api_component/               # 📋 FastAPI routers
│   └── tests/                            # 📋 0 tests
```

Update `📋` to `✅` as each layer is completed.

---

## Required files checklist — new module

When creating a brand new module, these files must exist before writing any implementation:

```
src/modules/<module_name>/
├── pyproject.toml                        # Poetry config (copy from another module, adjust name)
├── Dockerfile                            # Copy from another module, adjust module name
├── README.md                             # 1-paragraph description
├── tests/
│   └── conftest.py                       # sys.path setup + event_loop fixture (see skill)
├── src/
│   └── __init__.py
└── .ai-context/
    ├── module-context.md                 # Use Template 1 above
    └── domain-model-guide.md            # Use Template 2 above
```

Also update before writing any implementation code:
- `/.ai-context/project-context.md` — add module entry (Template 4)
- `/.ai-context/PROJECT_STRUCTURE_MAP.md` — add module entry (Template 6)
- `/.ai-context/adr/ADR-INDEX.md` — add governing ADR if one was written
- `docker-compose.yml` — add service block (port, env, depends_on db + migrate)
