# ADR-045: Frontend Architecture — Turborepo Monorepo + Next.js 14 App Router

**Status:** Proposed  
**Date:** 2026-04-19  
**Authors:** Development Team  
**Related ADRs:** ADR-007 (Auth Module), ADR-006 (API Layer Design), ADR-017 (Winery API), ADR-020 (Analysis Engine), ADR-040 (Alerts Strategy)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> - [Project Context](../project-context.md) - Estado actual del sistema

---

## Context

The backend (4 FastAPI microservices on ports 8000–8003) is 100% complete with 1,416 passing tests. The Frontend Module is the final remaining piece of the MVP. The interface must support remote fermentation monitoring from any device (mobile-first per `project-context.md`), enforce multi-tenant data isolation (`winery_id` always from JWT — never a UI prop), and be architected so that a future Expo mobile app can share validation schemas, formatters, and API hooks without duplication. No frontend code exists yet — this is a greenfield decision.

---

## Decision

1. **Turborepo monorepo at `frontend/`** in the project root, managed with pnpm workspaces. Structure: `apps/web`, `apps/mobile` (future), `packages/ui`, `packages/shared`.

2. **`packages/ui` — zero React, zero browser APIs.** Only Zod validation schemas, pure formatter functions, and display constant maps. Runs identically in Node (Vitest), Next.js, and React Native (Expo) with no polyfills.

3. **`packages/shared` — Axios + TanStack Query v5 hooks.** Contains `ApiClient` class with 401 auto-refresh, typed API function factories, React hooks, `TokenStorage` interface, and `SyncQueue`. Depends on `@wine/ui`. Portable to Expo via injectable `TokenStorage` (cookies on web, Expo SecureStore on mobile).

4. **`apps/web` — Next.js 14 App Router.** Route groups `(auth)` (unauthenticated) and `(dashboard)` (protected with role guard). Shadcn/ui components with a wine-domain theme (Cormorant Garamond display, burgundy `#8B1A2E` accent). Tailwind CSS for styling.

5. **Dev proxy via `next.config.ts` rewrites.** `/api/fermentation/*` → `:8000`, `/api/winery/*` → `:8001`, `/api/fruit-origin/*` → `:8002`, `/api/analysis/*` → `:8003`. Production routing continues to use the existing Nginx gateway (`docker/nginx/nginx.conf`) — no changes required there.

6. **TanStack Query v5 for all server state; Zustand for client-only state.** No Redux. TanStack Query handles caching, background refetch, and stale-while-revalidate. Zustand holds in-memory user state synced from the `currentUser` query.

7. **`winery_id` sourced exclusively from JWT.** `ApiClient` attaches `Authorization: Bearer <token>` on every request; the backend enforces tenant scoping. No UI component receives `winery_id` as a prop — this is a hard architectural constraint, enforced by convention and code review.

8. **Factory pattern for shared hooks.** `makeUseAuth(client)` and `makeUseCurrentUser(client)` return bound hooks rather than importing a global singleton. Each app injects its own `ApiClient` with the appropriate `TokenStorage` implementation.

9. **Testing: Vitest + React Testing Library + MSW.** TDD (RED → GREEN → REFACTOR) consistent with the project's established methodology. `packages/ui` tests run in Node environment; `packages/shared` and `apps/web` in jsdom.

---

## Implementation Notes

```
frontend/
├── package.json                   ← root workspace (pnpm@9, turbo)
├── pnpm-workspace.yaml
├── turbo.json                     ← task pipeline (build, dev, test, type-check, lint)
├── packages/
│   ├── ui/                        ← @wine/ui — zero React
│   │   └── src/
│   │       ├── schemas/           ← Zod schemas matching backend Pydantic DTOs
│   │       ├── formatters/        ← pure functions: formatDensity, formatBrix, etc.
│   │       └── constants/         ← display maps: FERMENTATION_STATUS_LABEL, etc.
│   └── shared/                    ← @wine/shared — Axios + TanStack Query
│       └── src/
│           ├── types/             ← TypeScript DTO interfaces (mirrors backend responses)
│           ├── api/               ← ApiClient + typed factory functions per domain
│           ├── hooks/             ← makeUseAuth, makeUseCurrentUser, usePolling, useRole
│           ├── storage/           ← TokenStorage interface + CookieTokenStorage
│           └── sync/              ← SyncQueue (offline support)
└── apps/
    └── web/                       ← @wine/web — Next.js 14
        └── src/
            ├── app/
            │   ├── (auth)/login/  ← unauthenticated route group
            │   └── (dashboard)/   ← protected route group (AdminLayout + AuthProvider)
            ├── providers/         ← QueryProvider, AuthProvider
            ├── lib/api-client.ts  ← singleton ApiClient with CookieTokenStorage
            ├── stores/            ← Zustand auth store
            └── components/layout/ ← Sidebar, Topbar, AdminLayout (role guard)
```

**Dependency direction** (mirrors backend Clean Architecture):
```
apps/web ──────────────────────────┐
apps/mobile (future) ──────────────┤──► packages/shared ──► packages/ui
                                   └──► packages/ui (direct, for schemas in forms)
```

**`ApiClient` 401 handling**: On 401 response, if not already refreshing, calls `/api/v1/auth/refresh`. Concurrent requests are queued via `refreshSubscribers` array and retried with the new token. On refresh failure, clears storage and throws `AuthExpiredError`.

**Multi-tenancy enforcement**: All four `AxiosInstance`s in `ApiClient` carry the same Bearer token. The backend's `winery_id` scoping (per ADR-007) means no frontend data structure ever needs to carry `winery_id` explicitly.

---

## Architectural Considerations

- **Deviation from standard `src/modules/` layout**: Frontend lives at `frontend/` (not `src/modules/frontend/`) because it is a full Turborepo workspace, not a Python module. This is consistent with the project-context note that the monorepo can host the frontend alongside backend services.
- **`packages/ui` with zero React**: Intentional over-constraint to ensure future Expo compatibility without code changes. All "display logic" (labels, colors, units) that doesn't need rendering lives here.
- **Cookie storage (not `httpOnly`)**: Tokens are accessible to JavaScript — acceptable for MVP, but should be revisited before public production deployment (consider BFF pattern with `httpOnly` cookies).

---

## Consequences

- ✅ Single codebase: Zod schemas and formatters shared — web and mobile validate identically, preventing drift
- ✅ `winery_id` never in component props — multi-tenant isolation enforced architecturally, not by discipline alone
- ✅ Dev proxy eliminates CORS friction during development
- ✅ TanStack Query handles polling (fermentation status every 30s) and stale data warnings natively
- ✅ `packages/ui` unit tests run in <1s (pure Node, no jsdom)
- ⚠️ `packages/shared` requires React as peer dependency — Expo must supply it (it does)
- ⚠️ Cookie token storage is not `httpOnly` — acceptable MVP trade-off, documented for future hardening
- ❌ `apps/mobile` not implemented in this phase — only package compatibility is guaranteed

---

## Related ADRs

- **[ADR-007](./ADR-007-auth-module-design.md)**: Defines the JWT auth endpoints (`/login`, `/refresh`, `/me`) this frontend consumes; `winery_id` scoping strategy originates here
- **[ADR-006](./ADR-006-api-layer-design.md)**: REST API design (FastAPI + Pydantic v2) whose response shapes are mirrored as TypeScript DTO types in `packages/shared/src/types/`
- **[ADR-017](./ADR-017-winery-api-design.md)**: Winery multi-tenancy enforcement — the ADMIN-only routes that drive the frontend role guard
- **[ADR-020](./ADR-020-analysis-engine-architecture.md)**: Analysis Engine API consumed by the frontend's analysis/recommendation hooks
- **[ADR-040](./ADR-040-notifications-alerts.md)**: Alert polling strategy (`usePolling` hook, 30s interval) designed to satisfy the "<15 seconds to log" mobile constraint

---

## TDD Plan

- `CreateFermentationSchema.safeParse({})` → `success: false` (missing required fields)
- `CreateFermentationSchema.safeParse({vintage_year: 2026, ...})` → `success: true`
- `formatDensity(1.0823)` → `'1.0823 g/cm³'`
- `formatDays(1)` → `'1 day'`, `formatDays(14)` → `'14 days'`
- `formatDeviationScore(-1.1)` → `'−1.1σ'`
- `new ApiClient({...})` → has `.fermentation`, `.winery`, `.fruitOrigin`, `.analysis` instances
- `new AuthExpiredError()` → `instanceof Error`, `message === 'Authentication expired'`
- `useAuthStore.getState().user` → `null` initially; `setUser({...})` → persists
- `LoginPage` → renders email field, password field, sign-in button
- `LoginPage` empty submit → shows "Email is required" validation error
- `AdminLayout` with WINEMAKER user on `/admin/*` → redirects to `/403`

---

## Quick Reference

- `packages/ui` = zero React, zero browser — Zod + formatters + constants only
- `packages/shared` = `ApiClient` + TanStack hooks + `TokenStorage` interface
- `winery_id` NEVER in component props — always from JWT via `ApiClient`
- Dev proxy: `next.config.ts` rewrites → ports 8000–8003
- Token storage: `CookieTokenStorage` (web), `SecureStoreTokenStorage` (mobile, future)
- 401 auto-refresh: queue concurrent requests, retry on success, throw `AuthExpiredError` on failure
- Role guard: `AdminLayout` blocks WINEMAKER from `/admin/*`, redirects to `/403`

---

## Status
Proposed
