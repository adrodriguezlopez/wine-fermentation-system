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

**Status**: 🔲 NOT STARTED — Phase 3 of FRONTEND-PLAN.md

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
