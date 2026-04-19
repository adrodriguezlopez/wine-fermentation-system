# Frontend Foundation — Session Starter Prompt

> Copy everything below this line into a new Claude Code session opened at `c:\dev\wine-fermentation-system`.

---

## Role

You are the implementing agent for the Wine Fermentation System frontend. The Python backend (4 microservices) is 100% complete. You are building the greenfield Next.js frontend from scratch inside a Turborepo monorepo.

## Project location

Working directory: `c:\dev\wine-fermentation-system`

Backend modules already running:
- `fermentation` → port 8000
- `winery` → port 8001
- `fruit_origin` → port 8002
- `analysis_engine` → port 8003

The frontend will live at `frontend/` (does not exist yet).

## Skills to load first

Before doing anything else, invoke all of these skills in a single message:

```
wine-frontend-context   — project API catalog, backend contracts, auth patterns
nextjs-app-router       — Next.js 14 App Router patterns and conventions
tanstack-query-v5       — TanStack Query v5 data fetching patterns
shadcn-ui               — Shadcn/ui component usage patterns
turborepo-monorepo      — Turborepo + pnpm workspaces setup
```

## Task

Implement the frontend foundation as defined in:

```
docs/superpowers/plans/2026-04-18-frontend-foundation.md
```

Use the `superpowers:executing-plans` skill to work through the plan task by task.

## Before writing any code — two mandatory steps

### Step 1: Write ADR-045

Use the `wine-adr` skill to write ADR-045 for the frontend architecture decisions. Key decisions to cover:
- Turborepo monorepo structure (`frontend/` at project root, not a separate repo)
- Package split: `packages/ui` (zero React, Zod/formatters/constants) vs `packages/shared` (Axios + TanStack Query hooks)
- Next.js 14 App Router with route groups for auth/protected areas
- Proxy strategy for 4 backend microservices (next.config.js rewrites)
- State management: TanStack Query for server state, Zustand for client state
- Multi-tenancy: `winery_id` comes from JWT, never passed explicitly by UI components

Wait for ADR review before proceeding to Step 2.

### Step 2: Create feature branch

```powershell
git checkout main
git pull
git checkout -b feat/frontend-foundation
```

## Constraints

- Follow Clean Architecture principles already established in the backend (dependency direction, separation of concerns)
- `packages/ui` must have zero React dependencies — it's shared with a future Expo mobile app
- `packages/shared` hooks must work in both Next.js and Expo
- `winery_id` must never appear in frontend component props — always sourced from JWT context
- All API calls go through the hooks in `packages/shared`, never direct fetch/axios calls from components
- Tests required: Vitest + React Testing Library for components, MSW for API mocking

## Context files to read before acting

```
/.ai-context/project-context.md                    — system overview, module list
/.ai-context/ARCHITECTURAL_GUIDELINES.md           — design principles
/.ai-context/adr/ADR-INDEX.md                      — existing decisions
```

There is no `frontend/` module-context.md yet — you will create it as part of the plan execution.
