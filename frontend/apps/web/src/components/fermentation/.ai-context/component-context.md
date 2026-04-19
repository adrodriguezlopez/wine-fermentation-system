# Component Context: Fermentation Components (`apps/web/src/components/fermentation/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: Fermentation endpoints in `.github/skills/wine-frontend-context/SKILL.md`

## Component responsibility

**All fermentation-related UI components** for the web admin app. This is the largest component group — it covers the fermentation list, creation form, the 5-tab detail page, sample recording, protocol step tracking, alerts management, corrective actions, and history timeline.

## Components

### List and creation
- **`FermentationTable.tsx`** — `<DataTable>` configured for fermentations. Columns: vessel code, vintage year, status badge, days fermenting, latest density, links. Status filter chips (ACTIVE/SLOW/STUCK/COMPLETED) above table. Search input filters by vessel code or vintage year. Framer Motion stagger on initial render.
- **`CreateFermentationForm.tsx`** — React Hook Form + `CreateFermentationSchema`. Fields: vessel code, vintage year, yeast strain, initial brix, input mass kg, start date. Toggle for "Blend mode" — switches to `BlendFermentationSchema` and renders `<BlendSourceSelector>`. Submits to `fermentationApi.createFermentation` or `createBlendFermentation`.
- **`BlendSourceSelector.tsx`** — Multi-select component for harvest lots. Each selected lot gets a percentage input. Validates that percentages sum to 100 (Zod refinement).

### Detail page — tab container
- **`FermentationDetailTabs.tsx`** — Shadcn `Tabs` with 5 tabs: Overview, Protocol, Alerts, Actions, History. Reads `fermentation.status` to show COMPLETED banner.

### Overview tab
- **`OverviewTab.tsx`** — `<ReadingsCard>` + `<DensityLineChart>` + `<StatCard>` grid + "Add Sample" trigger button.
- **`ReadingsCard.tsx`** — Displays latest sample values: density (DM Mono, large), temperature, brix. Shows `formatRelative(latest_sample.recorded_at)` timestamp. Polling via `usePolling` every 30s.
- **`AddSampleDrawer.tsx`** — `<Drawer>` containing `<SampleForm>`. Triggered by "Add Sample" button in OverviewTab.
- **`SampleForm.tsx`** — React Hook Form + `SampleSchema`. Sample type select (from `SAMPLE_TYPE_LABEL` constants), value input (DM Mono), datetime picker, notes textarea. Calls `sampleApi.createSample`. Invalidates `['samples', fermentationId]` query on success.

### Protocol tab
- **`ProtocolTab.tsx`** — Shows `<StepChecklist>` if active execution exists. Shows `<StartExecutionForm>` if no execution. Shows completed summary if execution is done.
- **`StepChecklist.tsx`** — Ordered list of `<StepRow>` from `GET /executions/{id}/steps`. Step number, type label, duration. Visual variants per step status.
- **`StepRow.tsx`** — Three variants:
  - `completed`: muted grey, checkmark icon, `formatDateTime(completed_at)`, click to view completion notes
  - `active`: wine-red left border, bold label, `<MarkCompleteForm>` below row
  - `upcoming`: grey text, no action
- **`MarkCompleteForm.tsx`** — Inline form below active step. Date + notes fields. `StepCompletionSchema` validation. Calls `executionApi.completeStep`.
- **`StartExecutionForm.tsx`** — Protocol selector dropdown + start date. Calls `executionApi.startExecution`.

### Alerts tab
- **`AlertsTab.tsx`** — Wraps `<AlertList>`. Shows pending count badge in tab header via polling.
- **`AlertList.tsx`** — List of `<AlertRow>` from `GET /executions/{id}/alerts`. Empty state when no pending alerts.
- **`AlertRow.tsx`** — Alert type label, description text, fermentation context. **Two buttons always present**:
  - "Acknowledge" → `POST /alerts/{id}/acknowledge` → button becomes muted, alert stays in list
  - "Dismiss" → `POST /alerts/{id}/dismiss` → alert removed from list
  These are never collapsed into one action.

### Actions tab
- **`ActionsTab.tsx`** — `<ActionTimeline>` + "Record Action" drawer trigger button.
- **`ActionTimeline.tsx`** — Chronological list of `<ActionCard>` from `GET /fermentations/{id}/actions`.
- **`ActionCard.tsx`** — Action type label, description, `formatDateTime(taken_at)`, outcome pill (pending/effective/ineffective). "Update Outcome" button if outcome is pending.
- **`RecordActionForm.tsx`** — `<Drawer>` with `ActionSchema` form. Action type select, description textarea, datetime, optional alert selector, optional recommendation selector.

### History tab
- **`HistoryTab.tsx`** — `<TimelineEventList>` from `GET /fermentations/{id}/timeline`.
- **`TimelineEvent.tsx`** — Icon per event type, description, `formatRelative(occurred_at)`.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
