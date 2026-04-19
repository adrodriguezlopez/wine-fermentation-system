# FermentationNote Feature — Architectural Decisions & ADR

## Overview

Before (or while) implementing the `FermentationNote` feature inside the fermentation module, several architectural decisions must be made explicit. After reading the existing codebase — entities, DTOs, repository interfaces, service, API router, and all relevant ADRs (ADR-002 through ADR-041) — I identified the decisions below, and created **ADR-042** to document them.

The ADR has been saved to:
```
.ai-context/adr/ADR-042-fermentation-note-feature.md
```

---

## Architectural Decisions That Needed Documentation

### 1. Entity Ownership — Child vs. Aggregate Root

**Question:** Should `FermentationNote` be its own aggregate root or a dependent child of `Fermentation`?

**Decision:** It is a child entity with a mandatory `fermentation_id` FK.

**Rationale:** Notes have no meaningful existence outside a fermentation. They are always queried in the context of their parent. Creating a separate aggregate root would violate the bounded context boundary and introduce unnecessary complexity.

---

### 2. Multi-Tenancy Scoping Strategy

**Question:** Should the `fermentation_notes` table carry its own `winery_id` column, or should tenant isolation be enforced through a JOIN to the `fermentations` table?

**Decision:** JOIN-based scoping — no `winery_id` on the notes table.

**Rationale:** This avoids data duplication and keeps the source of truth for tenant ownership in one place (`fermentations.winery_id`). The repository layer enforces the JOIN transparently for all callers. This is consistent with ADR-025 and is safe at expected data volumes. A denormalised column can be added as a non-breaking migration if cross-fermentation note queries become a performance concern.

---

### 3. Service Layer — Separate Class vs. Extension of FermentationService

**Question:** Should note operations be added to the existing `FermentationService` or encapsulated in a new `FermentationNoteService`?

**Decision:** Separate `FermentationNoteService` class.

**Rationale:** Single Responsibility Principle (SRP, ADR-005). Note CRUD is a distinct concern from fermentation lifecycle management. A separate service also allows it to raise its own typed exception (`FermentationNoteNotFoundError`) without polluting the fermentation error space.

---

### 4. DTO Validation Strategy

**Question:** Where should input validation for note creation/update live — in Pydantic request schemas, in the service, or in the DTOs themselves?

**Decision:** Validation in dataclass `__post_init__` on the DTOs (`FermentationNoteCreate`, `FermentationNoteUpdate`).

**Rationale:** Keeps validation at the domain boundary. The service layer builds DTOs from raw inputs; if a DTO is invalid, a `ValueError` is raised before any repository call. Pydantic schemas in the API layer handle HTTP-level coercion but are separate from domain rules. This matches the pattern established in ADR-005.

---

### 5. Soft Delete vs. Hard Delete

**Question:** Should notes support physical deletion?

**Decision:** Soft delete only, via an `is_deleted` boolean flag.

**Rationale:** Notes form part of the qualitative audit trail for a fermentation. Permanent deletion would destroy historical evidence that may be required for compliance or quality-review purposes. This is consistent with the soft-delete convention used by all other entities in the system.

---

### 6. REST API URL Design

**Question:** Should all note endpoints live under `/fermentations/{fermentation_id}/notes/*`, or should some use a flat `/notes/*` namespace?

**Decision:** Two URL families:
- **Nested** (`/fermentations/{fermentation_id}/notes`) for collection operations (create, list) where the parent context is essential.
- **Flat** (`/notes/{note_id}`) for singleton operations (get, update, delete) where the note ID is sufficient to resolve context.

**Rationale:** Nested paths make the parent-child relationship visible for writes and collection reads. Flat paths avoid verbose double-ID URLs for singleton access (the repository already validates tenant via JOIN). This is consistent with the REST design choices made for samples in ADR-006.

---

### 7. SQLAlchemy Relationship Configuration

**Question:** How should the ORM relationship between `FermentationNote` and `Fermentation` be configured to avoid registry conflicts?

**Decision:** Use fully-qualified class path string in `relationship()`. Standard bidirectional relationship (not `viewonly=True`) because no polymorphic inheritance conflict exists for this entity.

**Rationale:** Follows the project-wide SQLAlchemy best practices in `ARCHITECTURAL_GUIDELINES.md` (derived from ADR-004). `extend_existing=True` is also set in `__table_args__` to allow safe re-registration in test fixtures.

---

### 8. Error Handling — Centralised Decorator vs. Inline

**Question:** Should the note router use the `@handle_service_errors` centralised decorator (ADR-008) or inline `try/except` blocks?

**Decision:** Inline `try/except` for the initial implementation; migration to the decorator is deferred as low-risk technical debt.

**Rationale:** The note service raises two error types (`EntityNotFoundError` from the repo, `FermentationNoteNotFoundError` from the service) that both map to HTTP 404. The centralised decorator would need to be extended to cover `FermentationNoteNotFoundError`. Deferring keeps the first implementation simple while the pattern remains documented for future cleanup.

---

## ADR Created

**File:** `.ai-context/adr/ADR-042-fermentation-note-feature.md`  
**Status:** Accepted  
**Date:** 2026-04-18

The ADR captures all eight decisions above in the project's standard light-template format, including consequences (benefits, trade-offs, limitations) and explicit notes on any deviations from the standard architectural guidelines.

---

## Summary Table

| # | Decision | Choice Made |
|---|----------|-------------|
| 1 | Entity ownership | Child of Fermentation (dependent entity) |
| 2 | Multi-tenancy | JOIN-based, no `winery_id` on notes table |
| 3 | Service layer | Separate `FermentationNoteService` (SRP) |
| 4 | DTO validation | Dataclass `__post_init__` (domain boundary) |
| 5 | Delete strategy | Soft delete only (`is_deleted` flag) |
| 6 | URL design | Nested for collections, flat for singletons |
| 7 | SQLAlchemy config | Fully-qualified paths + `extend_existing=True` |
| 8 | Error handling | Inline `try/except` (decorator migration deferred) |
