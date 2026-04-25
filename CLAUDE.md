# Wine Fermentation System — Claude Code Instructions

## Project Skills

Skills live in `.claude/skills/` and are loaded automatically by the `Skill` tool.
Use the `Skill` tool (not `Read`) for all skills below.

| Skill name | When to use |
|---|---|
| `wine-adr` | Any architectural decision |
| `wine-backend-dev` | Any backend feature or bugfix |
| `wine-frontend-context` | Any frontend feature, UI component, or API integration |
| `frontend-design` | UI/UX design decisions |
| `nextjs-app-router` | Next.js App Router patterns |
| `tanstack-query-v5` | TanStack Query / React Query usage |
| `shadcn-ui` | shadcn/ui components |
| `turborepo-monorepo` | Turborepo / monorepo configuration |
| `skill-creator` | Creating or editing skills |

**Additional rule for frontend DTO/type work:** After invoking `wine-frontend-context`,
also read the actual backend `*_responses.py` and `*_schemas.py` files before writing
TypeScript types. Never trust plan-provided types without verifying against the real backend source.

## Project Overview

Wine Fermentation System — Python FastAPI backend (4 microservices) + Next.js frontend.

- **Backend:** `src/` — 4 microservices on ports 8000–8003 (fermentation, winery, fruit_origin, analysis_engine)
- **Frontend:** `frontend/` — Turborepo monorepo with Next.js 14 App Router
- **Architecture context:** `.ai-context/project-context.md`
- **ADR index:** `.ai-context/adr/ADR-INDEX.md`
