# Frontend Architecture — Current State

## What Exists Today

The web app lives in `frontend/apps/web` and is only partially implemented.

Current route files:

- `src/app/page.tsx` — root redirect based on session cookies
- `src/app/403/page.tsx` — forbidden page
- `src/app/(auth)/login/page.tsx` — login screen
- `src/app/(dashboard)/dashboard/page.tsx` — current dashboard page
- `src/app/(auth)/layout.tsx` — auth route wrapper
- `src/app/(dashboard)/layout.tsx` — authenticated shell with sidebar and topbar
- `src/app/layout.tsx` — root layout with `QueryProvider`

Current reusable layout components:

- `src/components/layout/sidebar.tsx`
- `src/components/layout/topbar.tsx`
- `src/components/layout/admin-layout.tsx`

Many other route/component directories exist only as scaffolding with `.gitkeep` files.

## What This Means For Implementation

Treat these areas as **planned but not implemented** unless you verify a real source file:

- `fermentations/`
- `protocols/`
- `analysis/`
- `admin/wineries/`
- most domain component folders under `src/components/`

Do not claim a screen or component exists just because its directory exists.

## File Placement Guidance

Use these boundaries:

- `apps/web/src/app/**` — route files, layouts, and route-local UI
- `apps/web/src/components/**` — reusable web UI components
- `apps/web/src/providers/**` — React providers tied to the web app shell
- `apps/web/src/stores/**` — client-side Zustand stores
- `apps/web/src/lib/**` — web-specific wiring such as `api-client.ts`
- `packages/shared/src/api/**` — reusable API modules shared across apps
- `packages/shared/src/types/**` — shared TypeScript domain types
- `packages/shared/src/hooks/**` — shared React hooks built on the shared API layer

## Current Composition Pattern

- Root layout stays lean and global.
- Dashboard layout owns authenticated chrome.
- Auth gating is currently applied inside the dashboard layout tree through `AuthProvider`.
- Shared packages should own transport/types when the concern is not web-only.

## Before Creating New Files

Check the nearest existing counterpart first:

- New route? Inspect neighboring route groups and layouts.
- New API integration? Inspect `packages/shared/src/api/` first.
- New domain type? Inspect `packages/shared/src/types/` first.
- New auth-aware client behavior? Inspect `apps/web/src/providers/` and `apps/web/src/stores/` first.

## Target Architecture vs Current Architecture

The repo contains plans for many more screens and components. Use those as **target direction**, not as evidence of completion.

When explaining or implementing work, be explicit about which of these is true:

- already implemented
- scaffolded only
- still planned