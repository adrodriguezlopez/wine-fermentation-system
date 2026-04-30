# Frontend Iteration 4: Fermentation Screens — Implementation Prompt

**Use this prompt in a fresh subagent thread to implement Iteration 4.**

---

## Overview

You are implementing **all fermentation domain screens** for an admin dashboard. The backend is complete and running. All screens must have **≥80% code coverage** using **Test-Driven Development (TDD)** with MSW for network mocking.

**Prerequisite:** Iteration 3 is merged to main. Branch from main: `feat/frontend-iteration-4-fermentations`.

---

## Architecture Summary (read all of these)

### Governing ADRs
- **ADR-045** (Frontend Architecture): Next.js 14 App Router, TanStack Query v5, Zustand auth store
- **ADR-047** (Polling Strategy): 30s standard interval, window focus Option C (continue + immediate refetch), stale thresholds 2min critical / 5min summary, stale banner UX
- **ADR-048** (MSW Testing): handlers organized by domain in `src/test/handlers/<domain>.ts`, registered globally in `setup.ts`, per-test overrides via `server.use(...)`

### Tech Stack
- **Framework:** Next.js 14 App Router
- **Styling:** Tailwind CSS + Shadcn/ui
- **Server state:** TanStack Query v5 (`useQuery`, `useMutation`, `refetchInterval`, polling disabled in tests)
- **Client state:** Zustand auth store
- **Forms:** React Hook Form + Zod (schemas from `@ui/schemas`)
- **Charts:** Recharts (density trend line on fermentation detail)
- **Icons:** lucide-react
- **Testing:** Vitest + React Testing Library + MSW, **minimum 80% coverage**

### Key Constraints
- **TDD mandatory:** Write failing test first, then implementation
- **MSW all the way:** No module mocks. All tests use MSW handlers at network layer
- **No URL-based tabs:** Visual tabs on detail page use `useState`, not URL search params. Analyses have sub-routes because they're independent entities.
- **Lab tech samples:** Samples can be recorded from web (desktop) — selector for type + value + datetime
- **Protocol optional:** Fermentations can exist without protocol (non-blocking banner on detail)
- **Stale UX:** 2min threshold for detail pages (critical), 5min for lists (summary), rendered as banner not error state

---

## Screen Inventory

### Dashboard Home (`/dashboard`)
- **KPI cards** (3 total):
  - Active fermentations count
  - Pending alerts count
  - Completed this month count
- Generic `<KpiCard>` component (extensible for future metrics)
- Active fermentations list below cards (first 5)
- Polling: 5min stale threshold

### Fermentation List (`/fermentations`)
- Filterable list (status, search by name)
- Filter state as single object: `{ status, search }`
- Each row: name, protocol, status, density trend sparkline, actions (edit/delete)
- "New fermentation" button top-right
- Polling: 5min stale threshold

### Create Fermentation (`/fermentations/new`)
- Form: name, winery (pre-selected from user context), protocol (optional), start date
- Type: `POST /api/fermentation/fermentations/create`
- Success: redirect to detail view

### Fermentation Detail (`/fermentations/[id]`)
- **Header:** Name, status badge, created date, actions (rename, delete)
- **5 visual tabs** (no URL change):
  1. **Overview:** Key metrics, sparkline chart (density over time)
  2. **Samples:** Table of all samples + "Record Sample" button (web form)
  3. **Protocol:** Assigned protocol or "None assigned" + selector to assign/change
  4. **Analyses:** List of analysis results + "Run Analysis" button
  5. **Alerts:** Real-time alerts (if active), historical (if completed), info banner (if none)
- Polling: 2min stale threshold (critical page)
- **No-protocol banner:** *"No protocol assigned — alerts and compliance tracking unavailable."* (visible but non-blocking)

### Record Sample Sub-form (modal/inline on Samples tab)
- Selector: type (`TEMPERATURE`, `DENSITY`, `SUGAR`, `ACETIC_ACID`)
- Value field (number)
- Datetime picker (defaults to now)
- Units displayed per type (fixed by backend: °C, specific gravity, brix, g/L)
- Success: adds row to table, clears form

### Analysis Detail (`/fermentations/[id]/analyses/[aid]`)
- Display analysis result data (recommendations, metrics)
- "View Recommendations" button → `/fermentations/[id]/analyses/[aid]/recommendations`

### Analysis Recommendations (`/fermentations/[id]/analyses/[aid]/recommendations/[rid]`)
- Show recommendation detail

---

## Implementation Tasks (12 total, TDD for each)

### Task 1: MSW Infrastructure + `renderWithProviders`
- [ ] Create `src/test/handlers/fermentation.ts` — global happy-path handlers (list, detail, create, samples, analyses, alerts)
- [ ] Register globally in `src/test/setup.ts`
- [ ] Create `src/test/utils.tsx` — `renderWithProviders` utility (wraps `render` with QueryClientProvider + auth store mock)
- [ ] Test: Verify `renderWithProviders` works and handlers are active
- **Coverage:** ≥80% on all new modules
- **Result:** PR ready for review, infrastructure solid before screens built

### Task 2: Dashboard Home
- [ ] Create `src/app/(dashboard)/dashboard/page.tsx` — 3 KPI cards + active fermentations list
- [ ] Create `<KpiCard>` component (generic, extensible)
- [ ] Hook up `useQuery` for fermentations + polling (5min stale)
- [ ] Tests: KPI rendering, polling behavior, list rendering
- **Coverage:** ≥80%

### Task 3: Fermentation List
- [ ] Create `src/app/(dashboard)/fermentations/page.tsx`
- [ ] Filter state: `useState({ status: null, search: '' })`
- [ ] Create `<FermentationListTable>` component with actions column
- [ ] Polling: 5min stale threshold
- [ ] Tests: list rendering, filter application, polling
- **Coverage:** ≥80%

### Task 4: Create Fermentation Form
- [ ] Create `src/app/(dashboard)/fermentations/new/page.tsx`
- [ ] Form: name, protocol (optional, select from list), start date
- [ ] Post to `POST /api/fermentation/fermentations/create`
- [ ] Redirect to detail on success
- [ ] Tests: form submission, error handling, redirect
- **Coverage:** ≥80%

### Task 5: Fermentation Detail Layout + Overview Tab
- [ ] Create `src/app/(dashboard)/fermentations/[id]/page.tsx`
- [ ] Render 5-tab layout (no URL change)
- [ ] Implement **Overview tab**: metrics + density trend chart (Recharts)
- [ ] No-protocol banner (conditional)
- [ ] Polling: 2min stale threshold
- [ ] Tests: tab switching, chart rendering, polling
- **Coverage:** ≥80%

### Task 6: Samples Tab + Record Sample Form
- [ ] Implement **Samples tab** in detail view
- [ ] Table of all samples (type, value, date)
- [ ] Modal/inline form: type selector, value field, datetime, submit button
- [ ] Form validation: value ranges per type
- [ ] Tests: sample list rendering, form submission, validation
- **Coverage:** ≥80%

### Task 7: Protocol Tab
- [ ] Implement **Protocol tab** in detail view
- [ ] Display assigned protocol or "None assigned"
- [ ] Selector to assign/change protocol (fetch list from API)
- [ ] Update via `PATCH /api/fermentation/fermentations/{id}`
- [ ] Tests: assignment, update, display
- **Coverage:** ≥80%

### Task 8: Analyses Tab + Run Analysis
- [ ] Implement **Analyses tab** in detail view
- [ ] List of all analyses (date, status, link to detail)
- [ ] "Run Analysis" button → `POST /api/analysis/analyses`
- [ ] Success: refresh list (invalidate query)
- [ ] Tests: list rendering, button click, API call
- **Coverage:** ≥80%

### Task 9: Alerts Tab
- [ ] Implement **Alerts tab** in detail view
- [ ] Real-time alerts when execution active (polling 30s)
- [ ] Historical alerts when execution completed
- [ ] Info banner when no alerts exist
- [ ] Tests: alert list rendering, state transitions
- **Coverage:** ≥80%

### Task 10: Analysis Detail View
- [ ] Create `src/app/(dashboard)/fermentations/[id]/analyses/[aid]/page.tsx`
- [ ] Fetch + display analysis result data
- [ ] "View Recommendations" button → sub-route
- [ ] Tests: data rendering, navigation
- **Coverage:** ≥80%

### Task 11: Recommendations Detail View
- [ ] Create `src/app/(dashboard)/fermentations/[id]/analyses/[aid]/recommendations/[rid]/page.tsx`
- [ ] Fetch + display recommendation detail
- [ ] Tests: data rendering
- **Coverage:** ≥80%

### Task 12: Integration + Full Coverage Audit
- [ ] Run `pnpm coverage` — verify ≥80% across all new files
- [ ] Fix any uncovered branches (missing test cases)
- [ ] Run `pnpm test` — all tests pass
- [ ] Run `pnpm type-check` — no TypeScript errors
- [ ] Git commit all work: `feat(web): implement fermentation screens with TDD`

---

## Testing Requirements (ADR-048)

**For each task:**

1. **Write test first** (Red):
   - Use `renderWithProviders` from `src/test/utils.tsx`
   - Use MSW handlers from `src/test/handlers/fermentation.ts`
   - For error cases: override handlers with `server.use(errorHandler)`

2. **MSW handler organization:**
   ```typescript
   // src/test/handlers/fermentation.ts
   export const handlers = [
     http.get('/api/fermentation/fermentations', () => {...}),
     http.post('/api/fermentation/fermentations/create', () => {...}),
     // etc.
   ]
   ```

3. **Test structure:**
   ```typescript
   import { render, screen } from '@testing-library/react'
   import { renderWithProviders } from '@/test/utils'
   import userEvent from '@testing-library/user-event'
   
   it('should display fermentations', async () => {
     renderWithProviders(<FermentationList />)
     await waitFor(() => {
       expect(screen.getByText(/active fermentations/i)).toBeInTheDocument()
     })
   })
   ```

4. **Coverage minimum:** ≥80% per file (measured by `pnpm coverage`)

5. **Polling tests:** Disable polling in tests via `refetchInterval: false` in test hooks, or mock timers

---

## Skills to Load

Before starting, read these skills:
- `.github/skills/wine-frontend-context/SKILL.md` — API endpoints, auth, data shapes
- `.github/skills/nextjs-app-router/SKILL.md` — routing patterns, layouts
- `.github/skills/shadcn-ui/SKILL.md` — component library usage
- `.github/skills/tanstack-query-v5/SKILL.md` — Query client setup, hooks, polling

---

## Branch & PR

**Branch:** `feat/frontend-iteration-4-fermentations` (branch from `main` after Iteration 3 merged)

**PR title:** `feat(web): implement fermentation screens (Iteration 4)`

**PR checklist:**
- ✅ All 12 tasks complete
- ✅ `pnpm test` passes (all tests green)
- ✅ `pnpm coverage` shows ≥80% on new files
- ✅ `pnpm type-check` passes
- ✅ No console warnings or errors
- ✅ Polling works per ADR-047 (2min detail, 5min list/dashboard)
- ✅ MSW handlers organized per ADR-048
- ✅ No direct commits to `main` (all work on feature branch)

---

## Success Criteria

**Done when:**
1. All 12 tasks implemented and tested
2. ≥80% code coverage on new files
3. All tests passing (green CI)
4. No TypeScript errors
5. PR open and ready for review
6. Backend integration verified (real API calls via proxy work)

---

## Notes

- **TDD:** Write test → see it fail → implement → see it pass → refactor
- **No mocking internals:** All network calls go through MSW; no module mocks for API client
- **Polling disabled in tests:** Use `refetchInterval: 0` or mock timers to prevent long-running tests
- **Stale thresholds:** 2min for detail pages (critical), 5min for lists — implement via `staleTime` in query options
- **80% coverage non-negotiable:** If a line is not covered, either delete it or write a test for it
