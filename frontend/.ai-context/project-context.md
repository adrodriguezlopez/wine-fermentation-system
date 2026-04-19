# Frontend Project Context — Wine Fermentation System

> **System Context**: See `/.ai-context/project-context.md` for backend system-level decisions
> **Full Plan**: See `frontend/FRONTEND-PLAN.md` for complete implementation plan
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md` for full endpoint + DTO reference
> **Design Guide**: See `.github/skills/frontend-design/SKILL.md` for design execution principles

---

## Frontend responsibility

The frontend delivers two separate user experiences over a complete, production-ready REST API backend:

1. **Admin Web** (`apps/web`) — desktop dashboard for winery administrators managing fermentations, protocols, fruit origin data, and winery settings
2. **Winemaker Mobile PWA** (`apps/mobile`) — mobile-first field tool for winemakers recording samples, tracking protocols, and responding to alerts

The `frontend/` folder is a **Turborepo monorepo** with two apps sharing logic through two local packages.

---

## Architecture

```
frontend/
├── apps/
│   ├── web/          ← Next.js 14 App Router (Admins, desktop)
│   └── mobile/       ← Expo SDK 52 + Expo Router v3 (Winemakers, mobile PWA)
├── packages/
│   ├── shared/       ← API client, TypeScript DTOs, auth/polling/offline hooks
│   └── ui/           ← Zod schemas, formatters, status/color constants
└── FRONTEND-PLAN.md  ← Full implementation plan
```

**Dependency flow**: `apps/*` → `packages/shared` → `packages/ui`. Apps never import from each other.

**Split-ready design**: Apps are self-contained. When split into separate repos, `packages/shared` becomes a private npm package.

---

## Users and roles

| Role | App | Use case |
|------|-----|---------|
| ADMIN | Web (`apps/web`) | Manage wineries, users; full visibility across all fermentations |
| WINEMAKER | Mobile PWA (`apps/mobile`) | Record samples in field; track protocol steps; respond to alerts |

Role is extracted from the JWT token. WINEMAKER attempting an ADMIN-only route is redirected to `/403`.

---

## Backend connection

The backend exposes 4 independent microservices:

| Service | Dev Port | Handles |
|---------|----------|---------|
| Fermentation | 8000 | Fermentations, samples, protocols, alerts, actions |
| Winery | 8001 | Winery management |
| Fruit Origin | 8002 | Vineyards, harvest lots |
| Analysis Engine | 8003 | Analyses, anomalies, recommendations, advisories |

In **development**: `apps/web` uses Next.js `rewrites` to proxy all `/api/*` requests to the correct port. `apps/mobile` uses `EXPO_PUBLIC_*_API_URL` env vars per service.

In **staging/production**: All traffic routes through the existing Nginx reverse proxy — no frontend config changes required.

---

## Key constraints

### Polling (no WebSockets)
The backend has no WebSocket support. Active fermentation data must be polled:
- **30-second interval** on: fermentation list, latest sample, alert count
- **Stop polling** when `fermentation.status === 'COMPLETED'`

### Alert UI — two distinct operations
Every alert row MUST render BOTH buttons:
- `POST /alerts/{id}/acknowledge` → alert stays visible, icon turns muted
- `POST /alerts/{id}/dismiss` → alert removed from list entirely

These are NOT interchangeable and must never be collapsed.

### Offline (mobile only)
- **Cache TTL**: 4 hours (one full shift). After 4h show stale data warning banner.
- **Write queue**: `SyncQueue` in `packages/shared` persists mutations to AsyncStorage, flushes on reconnect.
- **Queued writes**: sample recording, action recording, action outcome update, step completion
- **Online-only**: auth, alert acknowledge/dismiss, protocol execution start

### Multi-tenancy
The `winery_id` is embedded in the JWT. The frontend NEVER asks the user to select a winery — all API responses are already scoped by the backend.

---

## Design direction

**Clinical precision** — data is the hero. Readings and measurements are foregrounded over decoration.

| Aspect | Choice |
|--------|--------|
| Palette | `#FAFAF8` bg, `#1A1A2E` text, `#8B1A2E` wine-red accent |
| Display font | Cormorant Garamond — fermentation names, page titles |
| Reading font | DM Mono — all numeric values (density, brix, temperature) |
| UI font | DM Sans — labels, buttons, navigation |
| Charts | Recharts line chart, `#8B1A2E` stroke, minimal grid, custom tooltip |
| Motion | Framer Motion staggered reveals (web); Expo Reanimated springs (mobile) |

---

## Testing approach

TDD is enforced across both apps, matching the backend's discipline.

| App | Test framework | API mocking |
|-----|---------------|-------------|
| `apps/web` | Vitest + React Testing Library | MSW |
| `apps/mobile` | Jest + React Native Testing Library | MSW |

Zod schemas in `packages/ui` are tested independently. API hook tests mock at the MSW layer, not at the module level.

---

## Module contexts

| Module | Context file |
|--------|-------------|
| `packages/shared` | `packages/shared/.ai-context/module-context.md` |
| `packages/ui` | `packages/ui/.ai-context/module-context.md` |
| `apps/web` | `apps/web/.ai-context/module-context.md` |
| `apps/mobile` | `apps/mobile/.ai-context/module-context.md` |
