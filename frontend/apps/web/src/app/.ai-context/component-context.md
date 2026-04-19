# Component Context: Pages / Routing (`apps/web/src/app/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Next.js App Router pages** — one `page.tsx` per route. Pages are thin: they compose feature components from `src/components/`, wire up TanStack Query hooks, and handle navigation. No business logic in page files.

## Architecture pattern

All pages are **client components** (`'use client'`). Pages compose components, pass props, and handle navigation. Data fetching via TanStack Query hooks (not `fetch` in `async` page functions).

## Files and responsibilities

| File | Description |
|------|-------------|
| `(auth)/login/page.tsx` | Renders `<LoginForm />`. On success navigates to `/dashboard` |
| `(dashboard)/layout.tsx` | Wraps `<ProtectedRoute>` + `<AdminLayout>`. Reads `useRole()` for sidebar rendering and admin route guard |
| `(dashboard)/dashboard/page.tsx` | Renders `<KpiCard>` grid + `<RecentFermentationsTable>` |
| `(dashboard)/fermentations/page.tsx` | Renders `<FermentationTable>` with filter + search. "New Fermentation" button opens modal |
| `(dashboard)/fermentations/new/page.tsx` | Renders `<CreateFermentationForm>`. On success navigates to detail page |
| `(dashboard)/fermentations/[id]/page.tsx` | Renders `<FermentationDetailTabs>` (5 tabs) |
| `(dashboard)/fermentations/[id]/analyses/page.tsx` | Renders `<AnalysisListTable>` |
| `(dashboard)/fermentations/[id]/analyses/[aid]/page.tsx` | Renders `<AnalysisReport>` |
| `(dashboard)/fermentations/[id]/analyses/[aid]/recommendations/[rid]/page.tsx` | Renders `<RecommendationDetail>` |
| `(dashboard)/protocols/page.tsx` | Renders `<ProtocolTable>` |
| `(dashboard)/protocols/new/page.tsx` | Renders `<ProtocolForm>` in create mode |
| `(dashboard)/protocols/[id]/page.tsx` | Renders `<ProtocolForm>` in edit mode + `<StepsList>` |
| `(dashboard)/fruit-origin/page.tsx` | Renders `<VineyardTable>` |
| `(dashboard)/fruit-origin/vineyards/new/page.tsx` | Renders `<VineyardForm>` |
| `(dashboard)/fruit-origin/vineyards/[id]/page.tsx` | Renders vineyard detail + `<HarvestLotTable>` |
| `(dashboard)/fruit-origin/vineyards/[id]/lots/new/page.tsx` | Renders `<HarvestLotForm>` |
| `(dashboard)/admin/wineries/page.tsx` | Renders `<WineryTable>` (ADMIN only — layout guard) |
| `(dashboard)/admin/wineries/new/page.tsx` | Renders `<WineryForm>` |
| `(dashboard)/admin/wineries/[id]/page.tsx` | Renders `<WineryForm>` in edit mode |
| `403/page.tsx` | Static access denied page with "Go back" button |

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
