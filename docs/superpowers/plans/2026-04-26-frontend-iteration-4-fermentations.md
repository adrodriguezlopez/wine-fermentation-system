# Frontend Iteration 4: Fermentation Screens

> **Governing ADRs:**
> - [ADR-045](../../.ai-context/adr/ADR-045-frontend-architecture.md) — Frontend Architecture
> - [ADR-047](../../.ai-context/adr/ADR-047-frontend-polling-strategy.md) — Polling Strategy
> - [ADR-048](../../.ai-context/adr/ADR-048-frontend-msw-testing-strategy.md) — MSW Testing Strategy
>
> **Skills to load before starting:**
> - `wine-frontend-context` → `.github/skills/wine-frontend-context/SKILL.md`
> - `nextjs-app-router` → `.github/skills/nextjs-app-router/SKILL.md`
> - `shadcn-ui` → `.github/skills/shadcn-ui/SKILL.md`
> - `tanstack-query-v5` → `.github/skills/tanstack-query-v5/SKILL.md`

**Goal:** Deliver all fermentation domain screens in `apps/web` — dashboard home, fermentation list, create form, detail view (5 tabs), and analysis detail. All tests green using MSW. Polling per ADR-047.

**Prerequisite:** Iteration 3 merged — `apps/web` layout shell, auth, login, role guard all working.

**Branch:** `feat/frontend-iteration-4-fermentations` (branch from main after Iteration 3 is merged)

---

## Architectural decisions captured in this plan

- **Tabs on detail page:** Visual tabs with local `useState` — no URL change between tabs. Analyses have their own sub-routes (`/fermentations/[id]/analyses/[aid]`) because they are independent linkable entities.
- **Filters architecture:** Filter state is a single object `{ status, search }` in `useState` — designed to extend toward additional filter keys without restructuring.
- **Protocol on create:** Optional selector — can be assigned later from the Protocol tab.
- **Sample recording on web:** Available (lab technicians use desktop). Selector for type (`TEMPERATURE`, `DENSITY`, `SUGAR`, `ACETIC_ACID`) + value field + datetime. Units are fixed per type (backend-enforced).
- **Alerts tab:** Shows real-time alerts when execution active (polling), historical when execution completed, informational message when no execution exists.
- **Fermentations without protocol:** Allowed. Non-blocking banner on detail: *"No protocol assigned — alerts and compliance tracking unavailable."*
- **Dashboard home:** KPI cards (active count, pending alerts, completed this month) + active fermentations list. `<KpiCard>` is a generic component designed for future extensibility.
- **Run Analysis:** Button in Analyses tab triggers `POST /analyses`. Backend also runs automatically.
- **MSW handlers:** Per ADR-048 — organized by domain in `src/test/handlers/fermentation.ts`, registered globally in `setup.ts`. Error cases use `server.use(...)` per test.
- **Stale thresholds:** Per ADR-047 — 2 min for fermentation detail + alerts, 5 min for dashboard + list.

---

## Pre-flight

- [ ] Read all skills listed above
- [ ] Confirm Iteration 3 is merged: `git log --oneline -3`
- [ ] Create branch: `git checkout -b feat/frontend-iteration-4-fermentations`
- [ ] Confirm `pnpm test` passes 7/7 in `apps/web`

---

## Task 1: MSW handler infrastructure + `renderWithProviders`

**Objective:** Create the global MSW handler infrastructure (ADR-048) before any screen is built. All subsequent tasks depend on this.

### Steps

**1.1** Create `src/test/handlers/fermentation.ts` with happy-path handlers:
- `GET /api/fermentation/fermentations` → list with 2 items, status `ACTIVE`
- `GET /api/fermentation/fermentations/:id` → single fermentation detail
- `GET /api/fermentation/fermentations/:id/samples` → list with 3 samples (one each: DENSITY, TEMPERATURE, SUGAR)
- `GET /api/fermentation/fermentations/:id/samples/latest` → most recent DENSITY sample
- `POST /api/fermentation/fermentations/:id/samples` → 201 with created sample
- `GET /api/fermentation/fermentations/:id/actions` → list with 1 action
- `POST /api/fermentation/fermentations/:id/actions` → 201 with created action
- `PATCH /api/fermentation/actions/:id/outcome` → 200 with updated action
- `POST /api/fermentation/fermentations` → 201 with created fermentation
- `GET /api/fermentation/executions/:id` → execution detail with `status: 'ACTIVE'`
- `GET /api/fermentation/executions/:id/alerts` → list with 1 unacknowledged alert
- `POST /api/fermentation/alerts/:id/acknowledge` → 200
- `POST /api/fermentation/alerts/:id/dismiss` → 200
- `GET /api/analysis/analyses/fermentation/:id` → list with 1 analysis
- `GET /api/analysis/analyses/:id` → analysis detail with anomalies + recommendations
- `POST /api/analysis/analyses` → 201 with triggered analysis

All response shapes must match `@wine/shared` DTO types exactly (TypeScript-typed).

**1.2** Create `src/test/handlers/index.ts` — re-exports all domain handler arrays.

**1.3** Update `src/test/setup.ts`:
- Import handlers from `./handlers`
- Pass to `setupServer(...handlers)` — replace any empty `setupServer()` call

**1.4** Create `src/test/utils.tsx` — `renderWithProviders` utility:
```tsx
const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchInterval: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
})

export function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  )
}
```
Reset `testQueryClient` cache in `beforeEach` to prevent test pollution.

### Tests
- `src/test/handlers/fermentation.test.ts` — verify handlers return correct shapes by calling them directly (no React needed): `resolve(handler.resolver(req, res, ctx))` → matches DTO interface. At minimum test the list and detail handlers.

### Acceptance criteria
- [ ] `src/test/handlers/fermentation.ts` exists with all handlers listed above
- [ ] `src/test/handlers/index.ts` exports all handlers
- [ ] `setup.ts` registers all handlers globally
- [ ] `renderWithProviders` is exported from `src/test/utils.tsx`
- [ ] All existing 7 tests still pass

---

## Task 2: TanStack Query hooks for fermentation domain

**Objective:** Create all data-fetching hooks in `apps/web/src/hooks/` for the fermentation domain. These wrap the shared API functions with TanStack Query, applying the polling config from ADR-047.

### Steps

**2.1** Create `src/hooks/use-fermentations.ts`:
- `useFermentations(filters: { status?: string; search?: string })` — `GET /fermentations`, `refetchInterval: 5 * 60 * 1000` (5 min, summary query per ADR-047), `refetchOnWindowFocus: true`
- `useFermentation(id: number)` — `GET /fermentations/{id}`, `refetchInterval: 2 * 60 * 1000` (2 min, critical)
- `useCreateFermentation()` — mutation, `POST /fermentations`, invalidates `['fermentations']` on success
- `useFermentationSamples(fermentationId: number)` — `GET /fermentations/{id}/samples`, `refetchInterval` tied to fermentation status (2 min if ACTIVE/SLOW/STUCK, `false` if COMPLETED)
- `useLatestSample(fermentationId: number)` — `GET /fermentations/{id}/samples/latest`, same polling logic
- `useRecordSample()` — mutation, `POST /fermentations/{id}/samples`, invalidates samples queries on success
- `useFermentationActions(fermentationId: number)` — `GET /fermentations/{id}/actions`, no polling
- `useRecordAction()` — mutation, `POST /fermentations/{id}/actions`
- `useUpdateActionOutcome()` — mutation, `PATCH /actions/{id}/outcome`

**2.2** Create `src/hooks/use-execution.ts`:
- `useExecution(executionId: number | undefined)` — `GET /executions/{id}`, `refetchInterval: 2 * 60 * 1000`, disabled when `executionId` is undefined
- `useExecutionAlerts(executionId: number | undefined)` — `GET /executions/{id}/alerts`, `refetchInterval: 2 * 60 * 1000`, disabled when undefined
- `useAcknowledgeAlert()` — mutation, `POST /alerts/{id}/acknowledge`, invalidates alerts on success
- `useDismissAlert()` — mutation, `POST /alerts/{id}/dismiss`, invalidates alerts on success

**2.3** Create `src/hooks/use-analyses.ts`:
- `useFermentationAnalyses(fermentationId: number)` — `GET /analyses/fermentation/{id}`, no polling
- `useAnalysis(id: number)` — `GET /analyses/{id}`, no polling
- `useTriggerAnalysis()` — mutation, `POST /analyses`, invalidates fermentation analyses on success

**2.4** Export all hooks from `src/hooks/index.ts`.

### Tests
- `src/hooks/use-fermentations.test.ts` — using `renderWithProviders` and MSW:
  - `useFermentations()` returns list of 2 fermentations from handler
  - `useFermentation(id)` returns single fermentation
  - `useCreateFermentation()` calls POST and invalidates list
- `src/hooks/use-execution.test.ts`:
  - `useExecutionAlerts(id)` returns alerts list
  - `useAcknowledgeAlert()` calls POST acknowledge endpoint
  - `useDismissAlert()` calls POST dismiss endpoint
- `src/hooks/use-analyses.test.ts`:
  - `useTriggerAnalysis()` calls POST /analyses

### Acceptance criteria
- [ ] All hooks created and exported
- [ ] Hook tests pass using MSW (no module mocks)
- [ ] `refetchInterval` is `false` for COMPLETED fermentations (verified in test with MSW override)

---

## Task 3: Dashboard home page

**Objective:** Build `/dashboard` — KPI cards + active fermentations list with polling.

### Steps

**3.1** Create `src/components/dashboard/kpi-card.tsx`:
```tsx
interface KpiCardProps {
  label: string
  value: number | string
  icon: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
}
```
Generic component. Styled with wine theme. Accepts any metric — designed for future extensibility.

**3.2** Create `src/components/dashboard/active-fermentations-list.tsx`:
- Calls `useFermentations({ status: 'ACTIVE' })`
- Renders a table/list of active fermentations with: name, status badge, latest density reading, days active, alert count
- Clicking a row navigates to `/fermentations/[id]`
- Shows stale banner if last successful fetch > 5 min ago (using `useStaleDataWarning` from `@wine/shared`)
- Empty state: *"No active fermentations"*

**3.3** Update `src/app/(dashboard)/dashboard/page.tsx`:
- KPI cards row: Active Fermentations, Pending Alerts, Completed This Month
- KPI data derived from `useFermentations` results (count from list, filter locally)
- Below: `<ActiveFermentationsList />`

### Tests
- `src/components/dashboard/kpi-card.test.tsx`:
  - Renders label and value
  - Renders icon
- `src/components/dashboard/active-fermentations-list.test.tsx`:
  - Renders 2 fermentations from MSW handler
  - Shows empty state when handler returns empty list (`server.use(...)` override)
  - Shows stale banner when MSW returns network error and threshold exceeded
- `src/app/(dashboard)/dashboard/dashboard.test.tsx`:
  - Renders 3 KPI cards
  - Renders active fermentations list

### Acceptance criteria
- [ ] Dashboard renders KPI cards with real data from `useFermentations`
- [ ] Active fermentations list polls per ADR-047 (5 min interval)
- [ ] Stale banner appears on poll failure after 5 min
- [ ] Navigating from list row goes to correct detail URL

---

## Task 4: Fermentation list page

**Objective:** Build `/fermentations` — full list with status filter + search.

### Steps

**4.1** Create `src/components/fermentation/fermentation-filters.tsx`:
```tsx
interface FermentationFilters {
  status: string   // '' = all
  search: string
}
interface Props {
  filters: FermentationFilters
  onChange: (filters: FermentationFilters) => void
}
```
Filter state is a single object — extensible to add more keys (date range, grape variety, etc.) without restructuring. Contains:
- Status dropdown: All / Active / Slow / Stuck / Completed
- Search input with debounce (300ms) — filters by fermentation name client-side

**4.2** Create `src/components/fermentation/fermentation-table.tsx`:
- Table with columns: Name, Status (badge), Grape Variety, Volume, Latest Density, Days Active, Alerts, Actions (View button)
- Status badge uses `FERMENTATION_STATUS_COLOR` from `@wine/ui`
- Loading state: skeleton rows
- Empty state: *"No fermentations found"*

**4.3** Create `src/app/(dashboard)/fermentations/page.tsx`:
- `useState<FermentationFilters>({ status: '', search: '' })`
- Calls `useFermentations(filters)`
- Renders `<FermentationFilters>` + `<FermentationTable>`
- "New Fermentation" button → `/fermentations/new`
- Stale banner at 5 min threshold

### Tests
- `src/components/fermentation/fermentation-filters.test.tsx`:
  - Renders status dropdown and search input
  - Calls `onChange` with updated filter object when status changes
  - Calls `onChange` with updated search after debounce
- `src/components/fermentation/fermentation-table.test.tsx`:
  - Renders 2 rows from MSW handler
  - Renders status badges
  - Shows skeleton on loading (`server.use(...)` with delayed response)
  - Shows empty state when list is empty
- `src/app/(dashboard)/fermentations/fermentations.test.tsx`:
  - Renders filter controls + table
  - "New Fermentation" button present

### Acceptance criteria
- [ ] Filter object pattern implemented (single object, not separate params)
- [ ] Search debounced at 300ms
- [ ] Status filter values match backend enum exactly
- [ ] Table navigates to detail on row click

---

## Task 5: Create fermentation form

**Objective:** Build `/fermentations/new` — form to create a fermentation with optional protocol selector.

### Steps

**5.1** Add MSW handlers to `src/test/handlers/fermentation.ts`:
- `GET /api/fermentation/protocols` → list with 2 protocol options (name, id)

**5.2** Add hook `useProtocols()` to `src/hooks/use-fermentations.ts` (or new `use-protocols.ts`):
- `GET /protocols` — no polling, used only for the selector

**5.3** Create `src/components/fermentation/create-fermentation-form.tsx`:
Using React Hook Form + Zod schema from `@wine/ui`. Fields:
- `name` — text, required
- `grape_variety` — text, required
- `volume_liters` — number, required, > 0
- `start_date` — date picker, required, defaults to today
- `notes` — textarea, optional
- `protocol_id` — select, optional. Options loaded from `useProtocols()`. Placeholder: *"No protocol (assign later)"*

On submit: `useCreateFermentation()` mutation → on success navigate to `/fermentations/[newId]`.

**5.4** Create `src/app/(dashboard)/fermentations/new/page.tsx`:
- Renders `<CreateFermentationForm />`
- Back link to `/fermentations`

### Tests
- `src/components/fermentation/create-fermentation-form.test.tsx`:
  - Renders all fields including protocol selector
  - Shows "No protocol" as default option in selector
  - Validation: name required, volume must be > 0
  - On valid submit, calls POST /fermentations via MSW
  - On success, navigates to `/fermentations/[id]`
  - Shows server error message on 422 response (`server.use(...)` override)

### Acceptance criteria
- [ ] Protocol selector is optional — form submits without protocol selected
- [ ] `CreateFermentationSchema` from `@wine/ui` used for validation
- [ ] Protocol list loaded from API (MSW in tests)
- [ ] Navigation to new fermentation detail on success

---

## Task 6: Fermentation detail page — shell + tabs

**Objective:** Build `/fermentations/[id]` with 5 visual tabs. No URL change between tabs.

### Steps

**6.1** Create `src/components/fermentation/fermentation-status-badge.tsx`:
- Maps `FermentationStatus` enum to colored badge using `FERMENTATION_STATUS_COLOR` from `@wine/ui`

**6.2** Create `src/components/fermentation/no-protocol-banner.tsx`:
- Non-blocking yellow info banner: *"No protocol assigned — alerts and compliance tracking unavailable."*
- Only rendered when `fermentation.execution_id` is null/undefined

**6.3** Create `src/components/fermentation/fermentation-tabs.tsx`:
```tsx
type TabId = 'overview' | 'samples' | 'alerts' | 'protocol' | 'actions'

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  hasExecution: boolean  // controls Alerts badge visibility
  alertCount: number
}
```
Tab bar component. Alerts tab shows badge with unacknowledged alert count.

**6.4** Create `src/app/(dashboard)/fermentations/[id]/page.tsx`:
- Calls `useFermentation(id)` — 2 min polling
- `useState<TabId>('overview')` for active tab
- Renders: fermentation name + status badge, `<NoProtocolBanner>` if no execution, `<FermentationTabs>`, tab content switch
- Stale banner at 2 min threshold
- Loading state: skeleton
- Error state: *"Fermentation not found"* with back link

### Tests
- `src/components/fermentation/fermentation-tabs.test.tsx`:
  - Renders all 5 tabs
  - Active tab has correct aria-selected
  - Alert badge shows count when `alertCount > 0`
  - Alert badge hidden when `alertCount === 0`
- `src/components/fermentation/no-protocol-banner.test.tsx`:
  - Renders when `hasExecution` is false
  - Does not render when `hasExecution` is true
- `src/app/(dashboard)/fermentations/[id]/fermentation-detail.test.tsx`:
  - Renders fermentation name from MSW handler
  - Renders status badge
  - Default tab is Overview
  - Clicking Samples tab switches content
  - Shows NoProtocolBanner when execution_id is null

### Acceptance criteria
- [ ] Tab switching is local state — no URL change, no remount
- [ ] NoProtocolBanner shown only when `execution_id` is null/undefined
- [ ] Polling stops when `status === 'COMPLETED'`
- [ ] Stale banner at 2 min threshold

---

## Task 7: Overview tab

**Objective:** Build the Overview tab content — fermentation summary + latest sample + density chart.

### Steps

**7.1** Create `src/components/fermentation/overview-tab.tsx`:
- Fermentation metadata: start date, grape variety, volume, days active (calculated from `start_date`)
- Latest sample card: value + unit + recorded_at (calls `useLatestSample(id)`, polled 2 min)
- Density trend chart (see 7.2)
- Statistics section: calls `GET /fermentations/{id}/statistics` — renders avg temperature, avg density, total samples

**7.2** Create `src/components/fermentation/density-chart.tsx`:
- Recharts `LineChart` — x axis: `recorded_at`, y axis: `value`
- Filters `useFermentationSamples` results to `sample_type === 'density'` only
- Wine-red stroke `#8B1A2E`, minimal grid, custom tooltip showing value + unit + datetime
- If fewer than 2 density samples: shows *"Not enough data to display chart"*

### Tests
- `src/components/fermentation/overview-tab.test.tsx`:
  - Renders latest sample value and unit
  - Renders statistics section
  - Shows "Not enough data" when only 1 density sample (MSW override)
- `src/components/fermentation/density-chart.test.tsx`:
  - Renders chart when 2+ density samples exist
  - Shows empty state with 1 sample

### Acceptance criteria
- [ ] Chart only uses DENSITY samples (filters by `sample_type`)
- [ ] Latest sample polls at 2 min interval
- [ ] Statistics section renders without crashing when data is empty

---

## Task 8: Samples tab

**Objective:** Build the Samples tab — historical table + record sample form.

### Steps

**8.1** Create `src/components/fermentation/samples-table.tsx`:
- Table columns: Type, Value + Unit, Recorded At, Recorded By
- `SAMPLE_TYPE_LABEL` from `@wine/ui` for type display
- `formatDensity`, `formatTemperature` etc. from `@wine/ui` for value display
- Sorted by `recorded_at` descending
- Loading skeleton, empty state: *"No samples recorded yet"*

**8.2** Create `src/components/fermentation/record-sample-form.tsx`:
Fields:
- `sample_type` — select: Temperature / Density / Sugar / Acetic Acid (maps to enum values)
- `value` — number input, required. Label and placeholder adapt to selected type (e.g. "Density (specific gravity)")
- `recorded_at` — datetime-local, defaults to now
- Units are NOT shown as input — they are fixed per type and set by the backend

On submit: `useRecordSample()` mutation → invalidates samples queries → form resets.

**8.3** Create `src/components/fermentation/samples-tab.tsx`:
- `<RecordSampleForm fermentationId={id} />`
- `<SamplesTable fermentationId={id} />`

### Tests
- `src/components/fermentation/samples-table.test.tsx`:
  - Renders 3 sample rows from MSW handler
  - Uses `SAMPLE_TYPE_LABEL` for type column
  - Shows empty state when list is empty
- `src/components/fermentation/record-sample-form.test.tsx`:
  - Renders type selector with 4 options
  - Label updates when type changes (e.g. "Density (specific gravity)")
  - Required validation on value field
  - On valid submit, calls POST via MSW, form resets
  - Submit button disabled while submitting

### Acceptance criteria
- [ ] All 4 sample types available in selector
- [ ] Units field absent from form (backend-enforced)
- [ ] On successful record, samples table refreshes (query invalidation)

---

## Task 9: Alerts tab

**Objective:** Build the Alerts tab — real-time alerts with acknowledge + dismiss per ADR-040.

### Steps

**9.1** Create `src/components/fermentation/alert-row.tsx`:
```tsx
interface Props {
  alert: AlertDto
  onAcknowledge: (id: number) => void
  onDismiss: (id: number) => void
}
```
- Alert message, severity badge, created_at
- **Both buttons always rendered:** "Acknowledge" (mutes icon, alert stays) and "Dismiss" (removes from list)
- Acknowledged alerts show muted icon but remain in list
- Per ADR-040: these are never collapsed into a single action

**9.2** Create `src/components/fermentation/alerts-tab.tsx`:
Three states:
1. **Execution active** → `useExecutionAlerts(executionId)` with 2 min polling. List of `<AlertRow>` components. Stale banner at 2 min.
2. **Execution completed** → same query, no polling. Banner: *"Protocol completed — showing historical alerts."*
3. **No execution** → message: *"No protocol assigned — alerts will appear here once a protocol is running."*

### Tests
- `src/components/fermentation/alert-row.test.tsx`:
  - Renders alert message and severity badge
  - Renders both Acknowledge AND Dismiss buttons (always present)
  - Acknowledge button calls `onAcknowledge` with correct id
  - Dismiss button calls `onDismiss` with correct id
  - Acknowledged alert shows muted icon
- `src/components/fermentation/alerts-tab.test.tsx`:
  - Shows alerts list when execution is active (MSW handler)
  - Shows "Protocol completed" banner when execution completed (MSW override)
  - Shows "No protocol" message when no execution (no executionId)
  - Calls acknowledge endpoint on button click

### Acceptance criteria
- [ ] Both Acknowledge and Dismiss buttons always rendered — never collapsed
- [ ] Polling active only when execution is active
- [ ] Historical alerts shown when execution completed (no polling)
- [ ] No-execution state shows informational message (not error)

---

## Task 10: Protocol tab

**Objective:** Build the Protocol tab — execution status + step completions.

### Steps

**10.1** Create `src/components/fermentation/protocol-tab.tsx`:
Two states:
1. **No execution** → same no-protocol banner + link: *"Assign a protocol to this fermentation"* (button that triggers `POST /fermentations/{id}/execute` via a protocol selector modal)
2. **Has execution** → `useExecution(executionId)`:
   - Protocol name, execution status badge, start date
   - Steps list: each step shows name, due date, completion status
   - `useExecution` completions from `GET /executions/{id}/completions`
   - Completed steps: green check. Overdue steps: red. Pending: grey.

**10.2** Create `src/components/fermentation/assign-protocol-modal.tsx`:
- Modal with protocol selector (same `useProtocols()` hook from Task 5)
- On confirm: `POST /fermentations/{id}/execute` with `{ protocol_id }`
- On success: invalidates fermentation query, closes modal

### Tests
- `src/components/fermentation/protocol-tab.test.tsx`:
  - Shows "Assign protocol" state when no execution
  - Shows execution detail when execution exists (MSW handler)
  - Steps rendered with correct status indicators
- `src/components/fermentation/assign-protocol-modal.test.tsx`:
  - Renders protocol selector
  - On confirm calls POST /execute endpoint via MSW
  - Closes on cancel

### Acceptance criteria
- [ ] Assign protocol flow calls `POST /fermentations/{id}/execute`
- [ ] Step completion status correctly derived from completions list
- [ ] No execution state shows actionable path (not just empty)

---

## Task 11: Actions tab

**Objective:** Build the Actions tab — log of winemaker interventions.

### Steps

**11.1** Create `src/components/fermentation/action-row.tsx`:
- Action type, description, recorded_at, outcome (if set)
- "Update Outcome" button → inline form or modal to `PATCH /actions/{id}/outcome`

**11.2** Create `src/components/fermentation/record-action-form.tsx`:
Fields:
- `action_type` — select (values from backend action types)
- `description` — textarea, required
- `recorded_at` — datetime-local, defaults to now

On submit: `useRecordAction()` → invalidates actions list.

**11.3** Create `src/components/fermentation/actions-tab.tsx`:
- `<RecordActionForm fermentationId={id} />`
- `<ActionsList fermentationId={id} />` — list of `<ActionRow>`
- Empty state: *"No actions recorded"*

### Tests
- `src/components/fermentation/action-row.test.tsx`:
  - Renders action type and description
  - Shows outcome if set
  - "Update Outcome" button present
- `src/components/fermentation/actions-tab.test.tsx`:
  - Renders 1 action from MSW handler
  - Empty state when list empty
  - Record form present
  - On submit calls POST /actions via MSW

### Acceptance criteria
- [ ] Record action form submits and refreshes list
- [ ] Update outcome calls PATCH /actions/{id}/outcome
- [ ] Empty state rendered correctly

---

## Task 12: Analyses tab + analysis detail page

**Objective:** Build the Analyses tab and the analysis detail sub-route.

### Steps

**12.1** Create `src/components/fermentation/analyses-tab.tsx`:
- List of analyses from `useFermentationAnalyses(id)` — no polling
- Each row: analysis date, status, anomaly count, recommendation count → link to `/fermentations/[id]/analyses/[aid]`
- "Run Analysis" button → `useTriggerAnalysis()` mutation → on success invalidates analyses list
- Loading state while trigger is in flight: button shows spinner, disabled
- Empty state: *"No analyses yet — run one to detect anomalies"*

**12.2** Create `src/app/(dashboard)/fermentations/[id]/analyses/[aid]/page.tsx`:
- Calls `useAnalysis(aid)`
- Sections:
  - **Anomalies** — list with type, severity badge, description, deviation score (`formatDeviationScore` from `@wine/ui`)
  - **Recommendations** — list with category, description, "Apply" button (`PUT /recommendations/{id}/apply`)
  - **Advisories** — from `GET /fermentations/{id}/advisories`, with acknowledge button
- Back link to `/fermentations/[id]` (returns to Analyses tab)

### Tests
- `src/components/fermentation/analyses-tab.test.tsx`:
  - Renders 1 analysis from MSW handler
  - "Run Analysis" button calls POST /analyses via MSW
  - Button disabled while mutation in flight
  - Empty state when no analyses
- `src/app/(dashboard)/fermentations/[id]/analyses/[aid]/analysis-detail.test.tsx`:
  - Renders anomalies section with deviation scores
  - Renders recommendations with Apply buttons
  - Apply button calls PUT /recommendations/{id}/apply via MSW

### Acceptance criteria
- [ ] "Run Analysis" uses `useTriggerAnalysis()` — invalidates list on success
- [ ] `formatDeviationScore` from `@wine/ui` used for deviation display
- [ ] Analysis detail is a proper sub-route (linkable URL)
- [ ] Back link returns to fermentation detail

---

## Next planning

After Iteration 4 is merged, the next iteration plans to write are:

- **Iteration 5 — Protocols + Fruit Origin screens** (`/protocols`, `/protocols/new`, `/protocols/[id]`, `/fruit-origin`, `/fruit-origin/vineyards/[id]`, `/fruit-origin/vineyards/new`)
- **Iteration 6 — Admin screens** (`/admin/wineries`, `/admin/wineries/new`, `/admin/wineries/[id]`) — ADMIN role only
- **Iteration 7 — apps/mobile** (Expo SDK 52 + Expo Router) — field winemaker experience, offline support via SyncQueue

---

## Final checks

- [ ] `pnpm vitest run` in `apps/web` — all tests pass, no skipped
- [ ] No module-level mocks of `@wine/shared` in any test (all go through MSW)
- [ ] No `refetchInterval` active in tests (verify `testQueryClient` config)
- [ ] Both Acknowledge and Dismiss buttons present on every AlertRow
- [ ] `FERMENTATION_STATUS_COLOR` and `SAMPLE_TYPE_LABEL` from `@wine/ui` used (no hardcoded strings)
- [ ] `formatDensity`, `formatTemperature`, `formatDeviationScore` from `@wine/ui` used in display
- [ ] Stale banners: 2 min for detail + alerts, 5 min for list + dashboard
- [ ] `<KpiCard>` accepts generic props (label, value, icon) — no fermentation-specific logic inside
- [ ] Polling stops on `status === 'COMPLETED'` (test with MSW override)
