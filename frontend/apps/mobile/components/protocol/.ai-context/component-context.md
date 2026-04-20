# Component Context: Mobile Protocol Checklist (`apps/mobile/components/protocol/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/fermentation/[id]/protocol.tsx`

## Component responsibility

**Protocol execution checklist** — the primary protocol interaction surface for winemakers. Shows all steps in the active execution, allows marking steps complete, and displays completion detail for finished executions.

## Components

### `StepChecklist.tsx`
Scrollable ordered list of `<StepRow>` from `GET /executions/{id}/steps`. Polls every 30s (`usePolling`). Shows execution progress header (e.g., "Step 3 of 7") and a `<StatusBadge>` for execution status. Stops polling when `status === 'COMPLETED'`.

If no active execution: shows "No protocol started" message.

### `StepRow.tsx`
Three visual variants depending on `step.status`:

| Variant | Visual | Action |
|---|---|---|
| `completed` | Muted, checkmark, `formatDateTime(completed_at)` | Tap to expand notes |
| `active` | Wine-red left border, bold, pulsing accent | "Mark Complete" button → opens `<MarkCompleteSheet>` |
| `upcoming` | Grey text, no action | Not interactive |

Step header: sequence number, step type label (from `STEP_TYPE_LABEL`), expected duration.

### `MarkCompleteSheet.tsx`
`<BottomSheet>` for marking the active step complete.  
Fields: completed date (default: now), notes textarea (optional).  
Validates with `StepCompletionSchema`.  
On submit: `executionApi.completeStep(executionId, stepId, data)`. Invalidates steps query.  
If offline: enqueued to `SyncQueue` as `POST /steps/{id}/complete`.

### `CompletionDetail.tsx`
Shown when execution status is `COMPLETED`. Summary card: total steps, completion date, duration, and a link to the Analysis screen for this fermentation.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
