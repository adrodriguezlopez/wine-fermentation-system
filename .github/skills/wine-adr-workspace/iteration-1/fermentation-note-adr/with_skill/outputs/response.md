# Response: FermentationNote ADR

## Should you write an ADR first?

**Yes — an ADR is required before touching code.**

`FermentationNote` involves:
- A new schema-backed entity (new table, new FKs — hard to undo)
- Non-obvious design choices: `winery_id` denormalization, immutability, soft-delete vs hard-delete, service placement (own service vs. embedded in FermentationService), ownership/authorization rules
- Cross-cutting concerns: multi-tenancy scoping, structured logging, existing repository (ADR-009) that needs a service + API to become useful

Under the project's ADR policy, all of these trigger a mandatory ADR.

---

## What I found

- **ADR-009** (Implemented) already created `FermentationNoteRepository` with 19 unit + 20 integration tests — the entity was anticipated but never formally designed.
- **Next ADR number**: 043 (last entry was ADR-042, 2026-04-18).
- No existing ADR covers the entity design, service layer, or API surface for notes.

---

## ADR written

**File**: `/.ai-context/adr/ADR-043-fermentation-note-entity.md`

### Key decisions in ADR-043

| Topic | Decision |
|---|---|
| Entity fields | id, fermentation_id, winery_id (denorm), author_id, content (text ≤4000), noted_at, soft-delete timestamps |
| Multi-tenancy | `winery_id` stored on note directly (join-free scoping, consistent with ADR-002) |
| Delete strategy | Soft-delete only; notes are audit records; no cascade delete from parent fermentation |
| Immutability | No update endpoint — notes cannot be edited after creation; delete + re-create is the correction flow |
| Service ownership | Dedicated `FermentationNoteService` (SRP — note lifecycle ≠ fermentation lifecycle) |
| API | 4 endpoints under `/fermentations/{id}/notes`: POST, GET list, GET one, DELETE |
| Repository | Existing `FermentationNoteRepository` (ADR-009) requires no structural change |

---

## Files changed

| File | Change |
|---|---|
| `/.ai-context/adr/ADR-043-fermentation-note-entity.md` | Created |
| `/.ai-context/adr/ADR-INDEX.md` | Row added for ADR-043 |
| `src/modules/fermentation/.ai-context/module-context.md` | Governing ADRs section added linking ADR-043 |

---

## Next step

ADR-043 is written and added to the index. Review and confirm the decision — particularly:
- Is immutability (no update endpoint) acceptable for your UX?
- Should `noted_at` be user-supplied or always server-set?

Use the `wine-backend-dev` skill when ready to implement.
