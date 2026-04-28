# Module Context: apps/web (Admin Dashboard)

> **Parent Context**: See `frontend/.ai-context/project-context.md` for frontend-level decisions
> **Full Screen Inventory**: See `frontend/FRONTEND-PLAN.md`
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md`
> **Design Guide**: See `.github/skills/frontend-design/SKILL.md`

## Module responsibility

**Admin web dashboard** for winery administrators. Provides full visibility and control over fermentations, protocols, fruit origin data, analysis results, and winery settings. Runs in a desktop browser.

**Audience**: ADMIN and WINEMAKER roles (ADMIN has additional access to `/admin/*` routes).

## Technology stack

- **Framework**: Next.js 14 (App Router) — `src/app/` directory with route groups
- **Styling**: Tailwind CSS + Shadcn/ui component primitives
- **Server state**: TanStack Query v5 — fetching, caching, polling, mutations
- **Client state**: Zustand — auth session, UI state (drawer open/close, active tabs)
- **Charts**: Recharts — density trend line chart on fermentation detail
- **Animations**: Framer Motion — staggered list reveals, page transitions
- **Forms**: React Hook Form + Zod resolver (schemas from `packages/ui`)
- **Icons**: lucide-react (thin-stroke style)
- **Testing**: Vitest + React Testing Library + MSW

## Route structure

```
src/app/
├── (auth)/
│   └── login/page.tsx
├── (dashboard)/
│   ├── layout.tsx                   ← sidebar + topbar + role guard
│   ├── dashboard/page.tsx
│   ├── fermentations/
│   │   ├── page.tsx
│   │   ├── new/page.tsx
│   │   └── [id]/
│   │       ├── page.tsx             ← 5-tab detail
│   │       └── analyses/
│   │           ├── page.tsx
│   │           └── [aid]/
│   │               ├── page.tsx
│   │               └── recommendations/[rid]/page.tsx
│   ├── protocols/
│   │   ├── page.tsx
│   │   ├── new/page.tsx
│   │   └── [id]/page.tsx
│   ├── fruit-origin/
│   │   ├── page.tsx
│   │   ├── vineyards/new/page.tsx
│   │   └── vineyards/[id]/
│   │       ├── page.tsx
│   │       └── lots/new/page.tsx
│   └── admin/
│       └── wineries/
│           ├── page.tsx
│           ├── new/page.tsx
│           └── [id]/page.tsx
└── 403/page.tsx
```

## Module interfaces

**Consumes**: `@shared/api`, `@shared/hooks`, `@shared/types`, `@shared/storage`, `@ui/schemas`, `@ui/formatters`, `@ui/constants`
**Dev proxy**: Next.js rewrites route `/api/*` to backend services (see `next.config.ts`)
**Auth**: `CookieTokenStorage` injected into `ApiClient` at app initialization (`src/lib/api-client.ts`)

## Key architectural decisions

### Route groups
`(auth)` group — no sidebar/topbar; login page standalone layout.
`(dashboard)` group — all protected routes share `layout.tsx` which wraps `ProtectedRoute` + `AdminLayout`.

### Role-based layout
`layout.tsx` in `(dashboard)` reads `useRole()`. If WINEMAKER hits `/admin/*`, redirects to `/403`. ADMIN sees full sidebar including admin section.

### Data fetching strategy
- Page components are **client components** (`'use client'`). TanStack Query handles loading/error states.
- No `getServerSideProps` / `generateStaticParams` — all data is user-specific and requires auth.

### Dev API proxy
`next.config.ts` rewrites (development only):
```
/api/fermentation/:path* → http://localhost:8000/api/v1/:path*
/api/winery/:path*       → http://localhost:8001/api/v1/:path*
/api/fruit-origin/:path* → http://localhost:8002/api/v1/:path*
/api/analysis/:path*     → http://localhost:8003/api/v1/:path*
```

## Implementation status

**Status**: ✅ FOUNDATION COMPLETE — Iteration 3 (2026-04-19)

**Delivered in foundation (Iteration 3):**
- Turborepo workspace scaffold: `apps/web` with Next.js 14 App Router, Tailwind CSS, Shadcn/ui wine theme (`--primary: 349 69% 32%`), Vitest + RTL + MSW
- `src/lib/api-client.ts` — `ApiClient` singleton with `CookieTokenStorage` and `baseURLs` for all 4 services
- `src/stores/auth-store.ts` — Zustand store (`user: UserDto | null`, `setUser`, `clearUser`)
- `src/providers/query-provider.tsx` — stable `QueryClient` via `useState`
- `src/providers/auth-provider.tsx` — syncs `makeUseCurrentUser` result to auth store, redirects to `/login` on error
- Route group layouts: `(auth)/layout.tsx` (passthrough), `(dashboard)/layout.tsx` (wraps `AuthProvider` + `Sidebar` + `Topbar`)
- `src/app/(auth)/login/page.tsx` — React Hook Form + Zod, calls `login(email, password)`, `isSubmitting` state
- `src/components/layout/sidebar.tsx` — role-based nav (ADMIN sees admin section, WINEMAKER does not)
- `src/components/layout/topbar.tsx` — user display + logout
- `src/components/layout/admin-layout.tsx` — role guard, redirects WINEMAKER from `/admin/*` to `/403`
- `src/app/(dashboard)/dashboard/page.tsx` — placeholder
- `src/app/403/page.tsx` — access denied page
- `src/app/page.tsx` — root redirect to `/dashboard`
- `next.config.ts` — dev proxy rewrites to ports 8000–8003
- `.env.local` / `.env.example` — `NEXT_PUBLIC_*_API_URL` vars

**Not yet implemented (next iterations):**
- Actual screen content: fermentation list/detail, protocols, fruit origin, admin/wineries
- TanStack Query hooks for each domain resource
- MSW handlers for integration tests
- Recharts density chart component
- Framer Motion animations

## Component contexts

| Component group | Context file |
|----------------|-------------|
| `src/app/` (routing/pages) | `src/app/.ai-context/component-context.md` |
| `src/components/layout/` | `src/components/layout/.ai-context/component-context.md` |
| `src/components/ui/` | `src/components/ui/.ai-context/component-context.md` |
| `src/components/charts/` | `src/components/charts/.ai-context/component-context.md` |
| `src/components/fermentation/` | `src/components/fermentation/.ai-context/component-context.md` |
| `src/components/analysis/` | `src/components/analysis/.ai-context/component-context.md` |
| `src/components/protocols/` | `src/components/protocols/.ai-context/component-context.md` |
| `src/components/fruit-origin/` | `src/components/fruit-origin/.ai-context/component-context.md` |
| `src/components/admin/` | `src/components/admin/.ai-context/component-context.md` |
