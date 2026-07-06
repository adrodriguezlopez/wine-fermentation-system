---
name: wine-frontend-dev
description: >
  Frontend implementation guidance for the Wine Fermentation System. Use when building or
  refactoring Next.js pages, React components, auth flows, TanStack Query integrations,
  forms, charts, or responsive UI in frontend/apps/web or the shared frontend packages.
  Also use when the user asks how to implement a screen, connect the UI to backend APIs,
  or align frontend work with the current repository structure.
when_to_use: >
  Trigger for requests about React, Next.js App Router, dashboard screens, login/session
  handling, polling, shared frontend types, API client usage, layout/components, or
  frontend architecture in this repository.
---

# Wine Fermentation System — Frontend Development

Use this skill for frontend implementation work in this repository. Keep it anchored to the
current codebase, not to aspirational screens or generic React recipes.

This skill is intentionally brief. Read the relevant reference file for the task at hand:

- `architecture-current-state.md` — actual route/component structure and where new code should live
- `auth-and-routing.md` — current token, cookie, redirect, and protected-layout behavior
- `data-fetching-and-api.md` — shared API client, rewrites, TanStack Query, and integration workflow
- `ui-forms-and-testing.md` — UI composition, forms, responsive behavior, and frontend validation

## Current Reality

- The frontend is **partially scaffolded**, not greenfield.
- The active web app lives in `frontend/apps/web`.
- Shared API clients and types live in `frontend/packages/shared`.
- The app uses **Next.js 14 App Router**, **TanStack Query v5**, **Zustand**, **React Hook Form**, and **Zod**.
- Auth currently uses **cookie-backed token storage** through the shared API client, with route gating layered on top.
- Many screen directories exist only as scaffolding (`.gitkeep`). Do not describe them as implemented unless you verify a real file.

## Working Rules

1. Start from the nearest real implementation file, not from this skill.
2. Prefer **server components by default**. Add `"use client"` only when the component needs browser APIs, hooks, event handlers, or client state.
3. Reuse `@wine/shared` types and API abstractions before creating new ones.
4. Keep a clear distinction between:
   - **current implementation**
   - **target architecture**
   - **missing scaffolding still to be built**
5. Do not reintroduce outdated guidance such as in-memory auth tokens or “everything is a client component”.
6. When adding a new feature, update the smallest relevant slice first, then validate.

## Implementation Workflow

1. Inspect the current route, layout, provider, or shared package that already controls the behavior.
2. Read the matching reference file from this skill directory.
3. Implement the smallest repo-aligned change.
4. Validate with the narrowest useful command.

Default validation commands:

```bash
pnpm --filter @wine/web type-check
pnpm --filter @wine/web test
pnpm --filter @wine/web lint
```

Prefer a narrower command when the touched area already has focused tests.

## Task Routing

**If the task is about login, redirects, current user, token refresh, or protected pages:**
Read `auth-and-routing.md`.

**If the task is about API calls, query keys, polling, cache invalidation, or adding a new backend integration:**
Read `data-fetching-and-api.md`.

**If the task is about where files belong, what is already implemented, or whether a route exists:**
Read `architecture-current-state.md`.

**If the task is about layout, forms, responsive UI, component composition, or frontend testing:**
Read `ui-forms-and-testing.md`.

## Anti-Patterns To Avoid

- Treating planned screens as if they already exist
- Building a parallel API client in `apps/web` when the shared client already owns the concern
- Storing auth state only in React context while ignoring the existing Zustand store and cookie-backed token storage
- Converting server layouts/pages to client components without a concrete need
- Adding large, speculative abstractions before a single working screen exists

## Skill Maintenance

When the frontend architecture changes, update the reference file that owns that topic instead of growing this file.

Keep `SKILL.md` as:

- an overview
- a routing layer
- a guardrail list

Push details into the reference files.