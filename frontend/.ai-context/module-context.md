# Module Context: frontend/ (Wine Fermentation System UI)

> **System Context**: See `/.ai-context/project-context.md` for system-level decisions
> **Governing ADR**: See `.ai-context/adr/ADR-045-frontend-architecture.md` for the full architecture decision
> **Full Plan**: See `frontend/FRONTEND-PLAN.md` for the complete screen-by-screen implementation plan
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md` for endpoint + DTO reference
> **Design Guide**: See `.github/skills/frontend-design/SKILL.md` for design execution principles

---

## Module responsibility

The `frontend/` directory is a **Turborepo monorepo** delivering two user experiences over the Wine Fermentation System backend:

1. **`apps/web`** — Admin web dashboard (Next.js 14 App Router). Desktop-first. ADMIN and WINEMAKER roles. Fermentation monitoring, protocol management, fruit origin tracking, and winery admin.
2. **`apps/mobile`** *(future)* — Winemaker mobile PWA (Expo SDK 52 + Expo Router). Field-facing: sample recording, protocol steps, alert response.

Logic shared across both apps lives in two local packages:
- **`packages/shared`** — ApiClient, TypeScript DTOs, auth/polling/offline hooks, TokenStorage
- **`packages/ui`** — Zod schemas, pure formatters, display constant maps (zero React)

---

## Workspace structure

```
frontend/
├── apps/
│   ├── web/          ← @wine/web — Next.js 14 (ADMIN + WINEMAKER)
│   └── mobile/       ← @wine/mobile — Expo SDK 52 (WINEMAKER, future)
├── packages/
│   ├── shared/       ← @wine/shared — ApiClient, hooks, types, storage, sync
│   └── ui/           ← @wine/ui — Zod schemas, formatters, constants (zero React)
├── package.json      ← pnpm workspace root (pnpm@9, turbo)
├── pnpm-workspace.yaml
└── turbo.json        ← task pipeline: build, dev, test, type-check, lint
```

**Dependency direction** (no cycles):
```
apps/web ──────────────────────────┐
apps/mobile ────────────────────── ┤──► packages/shared ──► packages/ui
                                   └──► packages/ui  (direct, for form schemas)
```

---

## Technology stack

| Layer | Technology |
|-------|-----------|
| Admin web app | Next.js 14 App Router |
| Mobile app (future) | Expo SDK 52 + Expo Router v3 |
| Shared logic | TypeScript (strict mode), Axios, TanStack Query v5 |
| Shared UI primitives | Zod v3, date-fns, tsup |
| Styling | Tailwind CSS + Shadcn/ui (web); NativeWind (mobile) |
| Client state | Zustand |
| Charts | Recharts (web) |
| Animations | Framer Motion (web); Expo Reanimated (mobile) |
| Forms | React Hook Form + Zod resolver |
| Icons | lucide-react (web) |
| Testing | Vitest + React Testing Library + MSW (web/shared/ui); Jest + RNTL + MSW (mobile) |
| Build tooling | Turborepo + pnpm workspaces |

---

## Key architectural constraints

### `winery_id` never in component props
All API responses are already tenant-scoped by the backend (JWT carries `winery_id`). No UI component ever receives `winery_id` as a prop. Violating this breaks multi-tenancy.

### `packages/ui` — zero React, zero browser APIs
Only Zod schemas, pure formatter functions, and constant maps. This ensures future Expo compatibility without polyfills or divergence.

### ApiClient — constructor injection, no global env reads
`new ApiClient({ baseURLs, tokenStorage })` — the package never calls `process.env` directly. Each app injects the appropriate `TokenStorage` implementation (cookies on web, Expo SecureStore on mobile).

### Factory pattern for hooks
`makeUseAuth(client)` and `makeUseCurrentUser(client)` return hooks bound to the injected client. No module-level singletons in `packages/shared`.

### No server-side rendering for data
All pages are client components (`'use client'`). No `getServerSideProps` or RSC data fetching — all data is user-specific and requires auth tokens that only exist client-side.

### Polling (no WebSockets)
The backend has no WebSocket support. Fermentation list, latest sample, and alert count are polled every **30 seconds**. Polling stops when `fermentation.status === 'COMPLETED'`.

### Alerts — two distinct operations
Every alert row MUST render both `acknowledge` (stays visible, muted) and `dismiss` (removed) buttons. These are never collapsed into a single action.

---

## Design direction

**Clinical precision** — data is the hero.

| Aspect | Choice |
|--------|--------|
| Background | `#FAFAF8` (warm white) |
| Text | `#1A1A2E` (near-black) |
| Accent | `#8B1A2E` (wine-red, `--primary: 349 69% 32%`) |
| Display font | Cormorant Garamond — fermentation names, page titles |
| Numeric font | DM Mono — all measurement values (density, brix, temperature) |
| UI font | DM Sans — labels, buttons, navigation |
| Charts | Recharts line, `#8B1A2E` stroke, minimal grid, custom tooltip |

---

## Governing ADRs

| ADR | Decision |
|-----|---------|
| [ADR-045](../.ai-context/adr/ADR-045-frontend-architecture.md) | Full frontend architecture — Turborepo, Next.js 14, TanStack Query v5, Zustand, Shadcn/ui |
| [ADR-046](../.ai-context/adr/ADR-046-frontend-module-context-file.md) | Establishes this context file as part of the frontend module convention |
| [ADR-007](../.ai-context/adr/ADR-007-auth-module-design.md) | JWT auth endpoints (`/login`, `/refresh`, `/me`); `winery_id` scoping from JWT |
| [ADR-006](../.ai-context/adr/ADR-006-api-layer-design.md) | REST API design (FastAPI + Pydantic v2) — response shapes mirrored as TypeScript DTO types |
| [ADR-017](../.ai-context/adr/ADR-017-winery-api-design.md) | Winery multi-tenancy — drives the ADMIN-only role guard |
| [ADR-020](../.ai-context/adr/ADR-020-analysis-engine-architecture.md) | Analysis Engine API consumed by the frontend's analysis/recommendation hooks |
| [ADR-040](../.ai-context/adr/ADR-040-notifications-alerts.md) | Alert polling strategy (30s interval, two distinct operations) |

---

## Module contexts

| Module | Context file |
|--------|-------------|
| `packages/shared` | `packages/shared/.ai-context/module-context.md` |
| `packages/ui` | `packages/ui/.ai-context/module-context.md` |
| `apps/web` | `apps/web/.ai-context/module-context.md` |
| `apps/mobile` | `apps/mobile/.ai-context/module-context.md` |

---

## Implementation status

**Status**: ✅ FOUNDATION COMPLETE — Iterations 1–3 (2026-04-19 → 2026-04-26)

**What is built:**
- Complete Turborepo workspace scaffold with all packages and `apps/web`
- `packages/ui`: Zod schemas, formatters, constants — all tested in Node environment
- `packages/shared`: ApiClient (401 auto-refresh), all DTO types, auth/user/polling hooks, TokenStorage, SyncQueue
- `apps/web` foundation: layout shell (Sidebar, Topbar, AdminLayout role guard), QueryProvider, AuthProvider, login page, auth store, api-client singleton, route groups, dev proxy, 403 page

**What comes next (Iteration 4+):**
- Actual screen content for all routes in `apps/web` (fermentation list/detail, protocols, fruit origin, admin)
- TanStack Query hooks for each domain resource (using MSW for tests)
- Recharts density chart
- Framer Motion animations
- `apps/mobile` (Expo) — after `apps/web` screens are complete
