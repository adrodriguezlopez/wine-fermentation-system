# Component Context: Mobile Actions (`apps/mobile/components/actions/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/actions/index.tsx`

## Component responsibility

**Corrective action recording and tracking** for winemakers. Actions are corrections or interventions taken on a fermentation (e.g., adding nutrients, adjusting temperature). Winemakers record them against a specific fermentation, optionally linked to an alert or recommendation.

## Components

### `ActionCard.tsx`
Card for a single corrective action.

Content:
- Action type label (from `ACTION_TYPE_LABEL`)
- Description text
- `formatDateTime(taken_at)` in DM Mono
- Outcome pill: `PENDING` (yellow) / `EFFECTIVE` (green) / `INEFFECTIVE` (red)
- Fermentation vessel code as context label

"Update Outcome" button shown when outcome is `PENDING`. Opens `OutcomeSheet`.

### `ActionForm.tsx`
`<BottomSheet>` form for recording a new corrective action.

React Hook Form + `ActionSchema`. Fields:
- Fermentation selector (dropdown from active fermentations)
- Action type (select from `ActionType` enum)
- Description (textarea)
- Taken at (datetime — defaults to now)
- Notes (optional)

`SyncQueue`-aware: if offline → enqueues as `POST /actions`. If online → calls `actionApi.createAction` directly.

After save: invalidates `['actions']` query (or updates optimistically).

### `OutcomeSheet.tsx`
`<BottomSheet>` for updating action outcome.

Fields: outcome (segmented control: EFFECTIVE / INEFFECTIVE), notes textarea.  
Calls `actionApi.updateActionOutcome`. If offline → enqueues as `PATCH /actions/{id}/outcome`.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
