# Frontend Implementation Plan — Wine Fermentation System

> **Backend Context**: See `/.ai-context/project-context.md` for system-level decisions
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md` for full endpoint + DTO reference
> **Design Reference**: See `.github/skills/frontend-design/SKILL.md` for design execution guide

---

## Architecture Summary

Turborepo monorepo with two deployable apps sharing logic packages.

| App | Audience | Platform | Framework |
|-----|----------|----------|-----------|
| `apps/web` | Admins | Desktop browser | Next.js 14 App Router |
| `apps/mobile` | Winemakers (field) | Mobile PWA | Expo SDK 52 + Expo Router v3 |

| Package | Purpose |
|---------|---------|
| `packages/shared` | API client, TypeScript DTOs, auth/polling/offline hooks |
| `packages/ui` | Zod schemas, formatters, status/color constants |

**Split-ready**: Each app is self-contained. When split, `packages/shared` becomes a private npm package consumed by both repos as a versioned dependency.

---

## Tech Stack Decisions

### Web (`apps/web`)
- Next.js 14 (App Router) — SSR/SSG + API route rewrites for dev proxy
- Tailwind CSS + Shadcn/ui — design system primitives
- TanStack Query v5 — server state, polling, offline persistence
- Zustand — client state (auth session, UI state)
- Recharts — density trend charts
- Framer Motion — page transitions and staggered list animations
- Vitest + React Testing Library + MSW — TDD

### Mobile (`apps/mobile`)
- Expo SDK 52 + Expo Router v3 — file-based navigation, PWA export
- NativeWind v4 — Tailwind-compatible styling for React Native
- TanStack Query v5 — same query hooks as web, with AsyncStorage persistence
- Zustand — client state
- Expo Reanimated — animated list items, BottomSheet springs
- Jest + React Native Testing Library + MSW — TDD

### Shared (`packages/shared`)
- TypeScript strict mode
- Axios — HTTP client with interceptors
- TanStack Query — base hook factories
- expo-secure-store (mobile) / js-cookie (web) — token storage

### Shared (`packages/ui`)
- Zod — form validation schemas (used in both web and mobile)
- date-fns — date formatting

---

## Design System

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#FAFAF8` | Page background |
| Surface | `#FFFFFF` | Cards, panels |
| Text primary | `#1A1A2E` | Body text |
| Accent | `#8B1A2E` | Wine red — CTAs, chart lines, active states |
| Muted | `#6B7280` | Secondary text, disabled states |
| Success | `#16A34A` | Completed status, applied recommendations |
| Warning | `#D97706` | Slow fermentation, medium confidence |
| Danger | `#DC2626` | Stuck fermentation, critical anomalies |

| Font role | Font family | Usage |
|-----------|-------------|-------|
| Display/headings | Cormorant Garamond | Page titles, fermentation names |
| Numeric readings | DM Mono | All measurement values (density, brix, temp) |
| UI text | DM Sans | Labels, body, buttons, navigation |

---

## Environment Configuration

### `apps/web` — `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

Next.js `rewrites` in `next.config.ts` proxy all `/api/*` to backend services (dev only):
- `/api/fermentation/**` → `http://localhost:8000/**`
- `/api/winery/**` → `http://localhost:8001/**`
- `/api/fruit-origin/**` → `http://localhost:8002/**`
- `/api/analysis/**` → `http://localhost:8003/**`

Production: single Nginx host — no rewrites needed.

### `apps/mobile` — `.env.local`
```
EXPO_PUBLIC_FERMENTATION_API_URL=http://localhost:8000
EXPO_PUBLIC_WINERY_API_URL=http://localhost:8001
EXPO_PUBLIC_FRUIT_ORIGIN_API_URL=http://localhost:8002
EXPO_PUBLIC_ANALYSIS_API_URL=http://localhost:8003
```

### `packages/shared`
Receives base URLs as constructor arguments — never reads `process.env` directly. This keeps the package portable across web and mobile.

---

## Screen Inventory

### Admin Web — 20 screens

| # | Path | Description |
|---|------|-------------|
| 1 | `/login` | Email + password auth form |
| 2 | `/dashboard` | KPI cards + recent fermentations table |
| 3 | `/fermentations` | Paginated list, status filter, search |
| 4 | `/fermentations/new` | Create form; blend mode toggle |
| 5 | `/fermentations/[id]` | Detail with 5 tabs: Overview (+ Add Sample drawer), Protocol (step checklist), Alerts, Actions, History |
| 6 | `/fermentations/[id]/analyses` | All analyses list with deviation score badges |
| 7 | `/fermentations/[id]/analyses/[aid]` | Full analysis report: anomalies, recommendations, historical comparison |
| 8 | `/fermentations/[id]/analyses/[aid]/recommendations/[rid]` | Recommendation detail + Apply CTA |
| 9 | `/protocols` | Protocol list + clone per row |
| 10 | `/protocols/new` | Create form |
| 11 | `/protocols/[id]` | Edit form + steps CRUD |
| 12 | `/fruit-origin` | Vineyards list |
| 13 | `/fruit-origin/vineyards/new` | Create vineyard |
| 14 | `/fruit-origin/vineyards/[id]` | Vineyard detail + harvest lots |
| 15 | `/fruit-origin/vineyards/[id]/lots/new` | Create harvest lot |
| 16 | `/admin/wineries` | All wineries — ADMIN only |
| 17 | `/admin/wineries/new` | Create winery |
| 18 | `/admin/wineries/[id]` | Edit winery |
| 19 | `/403` | Access denied (role guard redirect) |

### Mobile Winemaker PWA — 15 screens

| # | Path | Description |
|---|------|-------------|
| 1 | `(auth)/login` | Login screen |
| 2 | `(tabs)/` | Fermentations list, status badges, alert badge, pull-to-refresh |
| 3 | `(tabs)/fermentation/[id]` | Detail: readings, Sample FAB, nav to protocol/analysis/alerts |
| 4 | `(tabs)/fermentation/[id]/sample/new` | Record sample (offline-queued) |
| 5 | `(tabs)/fermentation/[id]/protocol` | Full step checklist: completed / active / upcoming |
| 6 | `(tabs)/fermentation/[id]/protocol/completions/[cid]` | Completion detail: date, notes |
| 7 | `(tabs)/fermentation/[id]/analysis` | Analysis summary + Run Analysis FAB |
| 8 | `(tabs)/fermentation/[id]/analysis/recommendations` | Recommendations list with Apply |
| 9 | `(tabs)/fermentation/[id]/analysis/advisories` | Protocol advisories with Acknowledge |
| 10 | `(tabs)/alerts` | All pending alerts: Acknowledge + Dismiss per row |
| 11 | `(tabs)/actions` | Recorded actions list |
| 12 | `(tabs)/actions/new` | Record corrective action (offline-queued) |
| 13 | `(tabs)/profile` | User info + logout |

**Total: 35 screens**

---

## Offline Strategy (Mobile)

**Cache**: TanStack Query + AsyncStorage persistence, 4-hour TTL.
- `networkMode: 'offlineFirst'` on: fermentation detail, latest sample, protocol execution steps
- Stale banner shown after 4 hours without network (`useStaleDataWarning`)

**Write queue**: `SyncQueue` persists mutations to AsyncStorage, flushes in order on reconnect.
- **Queued (work offline)**: `POST /samples`, `POST /actions`, `PATCH /actions/{id}/outcome`, `POST /steps/{id}/complete`
- **Requires online**: auth, alert acknowledge/dismiss, protocol execution start

---

## Auth Flow

```
Login → POST /auth/login → { access_token (15min), refresh_token (7d) }
       ↓
Store: httpOnly cookie (web) / SecureStore (mobile)
       ↓
All requests: Authorization: Bearer <access_token>
       ↓
401 received → POST /auth/refresh → new access_token → retry original request
       ↓
Refresh fails → clear tokens → redirect to /login
```

---

## Role Guards

| Role | Access |
|------|--------|
| ADMIN | All screens including `/admin/*` |
| WINEMAKER | All screens except `/admin/*`; hitting admin route → `/403` |

---

## Polling Strategy

Active fermentation data refreshes every 30 seconds on:
- `GET /fermentations` (dashboard list)
- `GET /fermentations/{id}/samples/latest` (fermentation detail)
- `GET /executions/{id}/alerts` (alert badge count)

Polling **stops** when `fermentation.status === 'COMPLETED'`.

---

## Alert UI Constraint

Both buttons are **always rendered** on every alert row:
- **Acknowledge**: marks as seen; alert stays in list (icon turns muted). Use for "I've read this."
- **Dismiss**: removes from active list entirely. Use for "I've acted on this."

These are two different API calls (`POST /alerts/{id}/acknowledge` vs `POST /alerts/{id}/dismiss`) and must never be collapsed into a single action.

---

## Component Inventory Summary

| Location | Groups | ~Components |
|----------|--------|-------------|
| `packages/shared/src/` | types, api, hooks, storage, sync | ~45 files |
| `packages/ui/src/` | schemas, formatters, constants | ~15 files |
| `apps/web/src/components/` | layout, ui, charts, auth, dashboard, fermentation, analysis, protocols, fruit-origin, admin | ~55 components |
| `apps/mobile/components/` | ui, fermentation, fermentation-detail, protocol, analysis, alerts, actions, profile | ~30 components |

---

## Implementation Phases

| Phase | Scope | Depends on |
|-------|-------|-----------|
| 0 | Environment + proxy config | — |
| 1 | Monorepo foundation (Turborepo, both apps, both packages) | Phase 0 |
| 2 | Shared API layer (ApiClient, all hooks) | Phase 1 |
| 3 | Admin web screens | Phase 2 |
| 4 | Offline + sync layer | Phase 2 |
| 5 | Mobile PWA screens | Phases 2 + 4 |
| 6 | Design system + polish | Phases 3 + 5 |

---

## Verification Checklist

- [ ] `pnpm -r build` — zero TypeScript errors across all packages
- [ ] `pnpm -r test` — all unit tests pass (TDD enforced)
- [ ] Web login → dashboard → fermentation detail → all 5 tabs render
- [ ] Overview tab: "Add Sample" drawer → sample appears in density chart within 30s
- [ ] Protocol tab: full step checklist with completed / active / upcoming variants
- [ ] Alert rows: both Acknowledge and Dismiss buttons always visible; correct behavior each
- [ ] Role guard: WINEMAKER navigates to `/admin/wineries` → redirected to `/403`
- [ ] Offline: airplane mode → record sample → reconnect → SyncQueue flushes to backend
- [ ] Stale banner: 4h without network refresh → dismissible banner appears on fermentation detail
- [ ] Mobile protocol: completed steps show date; only active step shows Mark Complete
- [ ] `pnpm --filter mobile export --platform web` → Lighthouse PWA installable, score ≥ 85
- [ ] Auth 401 recovery: force 401 → refresh fires → original request retried → user stays logged in
