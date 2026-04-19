# ADR-043: FermentationNote Entity Design

**Status:** Proposed  
**Date:** 2026-04-19  
**Authors:** Wine Fermentation System Team

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

Winemakers need to attach free-text notes to fermentations — observations, interventions, tasting impressions — timestamped and associated with a specific fermentation. The fermentation module already has a `FermentationNoteRepository` (implemented in ADR-009 with 19 unit + 20 integration tests), confirming the entity was anticipated but never formally specified. The entity design requires decisions on ownership scoping (winery_id vs. fermentation FK), soft-delete strategy, service placement, and API surface — none of which follow trivially from existing patterns and all of which are hard to undo once the schema is in production.

---

## Decision

1. **Entity**: `FermentationNote` belongs to the fermentation module's domain layer with fields: `id` (UUID), `fermentation_id` (FK → fermentations), `winery_id` (FK → wineries, denormalized for multi-tenant query performance), `author_id` (FK → users), `content` (text, non-nullable, max 4000 chars), `noted_at` (timestamp with timezone, defaulting to now()), `created_at`, `updated_at`, `deleted_at` (soft-delete).
2. **Multi-tenancy**: `winery_id` is stored directly on `FermentationNote` (denormalized from its parent Fermentation) so all note queries can be scoped by `winery_id` without a join, following the established pattern from ADR-002.
3. **Delete strategy**: Soft-delete only (set `deleted_at`). Notes are audit records — hard deletion is not allowed. Deleting the parent fermentation does not cascade-delete notes; notes are retained for the audit trail.
4. **Ownership**: A note is owned by the winemaker who created it (`author_id`). Any winemaker within the same winery may read all notes for a fermentation they can access. Only the note author or an ADMIN may delete a note.
5. **Service placement**: `FermentationNoteService` is added to the fermentation module's service component. It does not live inside `FermentationService` (SRP: note lifecycle is distinct from fermentation lifecycle).
6. **API endpoints** (fermentation-scoped): `POST /fermentations/{id}/notes`, `GET /fermentations/{id}/notes`, `GET /fermentations/{id}/notes/{note_id}`, `DELETE /fermentations/{id}/notes/{note_id}` — no update endpoint (notes are immutable once written; if correction is needed, delete and re-create).
7. **Schema migration**: A new Alembic migration creates the `fermentation_notes` table with the columns above; existing `FermentationNoteRepository` implementation (ADR-009) is the concrete repository and requires no structural change.

---

## Architectural Notes

> Seguimos [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) por defecto

**Deviation — no update endpoint**: Notes are intentionally immutable. Allowing in-place edits would destroy the audit value of a timestamped record. Delete + re-create is the supported correction flow.

**Denormalized `winery_id`**: Consistent with ADR-002's multi-tenancy scoping pattern. Saves a join on every list query and ensures notes cannot be orphaned into a cross-winery state.

---

## Consequences

- ✅ Winemakers can attach timestamped observations to fermentations, supporting the "intelligent decision support" goal of ADR-020
- ✅ `FermentationNoteRepository` (ADR-009) is already implemented and tested; this ADR unblocks completing the service + API layers
- ✅ Immutable notes provide a reliable audit trail for compliance and deviation review (complements ADR-021 protocol compliance)
- ✅ Multi-tenant scoping via `winery_id` is consistent with all other entities; no new patterns introduced
- ⚠️ Denormalized `winery_id` must be kept in sync on write; a validator must enforce that `note.winery_id == fermentation.winery_id` at creation time
- ⚠️ No update endpoint means correction requires delete + re-create; UX must communicate this clearly
- ❌ Notes are never hard-deleted; storage grows over time (accepted — notes are small text records)

---

## Related ADRs

- **ADR-002**: Repository Architecture — multi-tenancy scoping pattern this ADR follows
- **ADR-003**: Repository SRP — one repository per aggregate root (FermentationNoteRepository is separate from FermentationRepository)
- **ADR-005**: Service Layer Interfaces — FermentationNoteService will follow the same typed-interface pattern
- **ADR-006**: API Layer Design — REST endpoint conventions and Pydantic v2 DTOs
- **ADR-009**: Missing Repositories — FermentationNoteRepository already implemented here
- **ADR-021**: Protocol Compliance Engine — notes may reference protocol deviations; read-only integration only
- **ADR-027**: Structured Logging — FermentationNoteService must log create/delete with LogTimer

---

## Status

Proposed
