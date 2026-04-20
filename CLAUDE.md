# Wine Fermentation System — Claude Code Instructions

## Project Skills

This project has custom skills in `.github/skills/`. The `Skill` tool **cannot** load them
(it only sees installed plugins and `.claude/` skills). When a skill is needed, read it directly
with the `Read` tool and follow its contents.

| Skill name | Path |
|---|---|
| `wine-adr` | `.github/skills/wine-adr/SKILL.md` |
| `wine-backend-dev` | `.github/skills/wine-backend-dev/SKILL.md` |
| `wine-frontend-context` | `.github/skills/wine-frontend-context/SKILL.md` |
| `frontend-design` | `.github/skills/frontend-design/SKILL.md` |
| `nextjs-app-router` | `.github/skills/nextjs-app-router/SKILL.md` |
| `tanstack-query-v5` | `.github/skills/tanstack-query-v5/SKILL.md` |
| `shadcn-ui` | `.github/skills/shadcn-ui/SKILL.md` |
| `turborepo-monorepo` | `.github/skills/turborepo-monorepo/SKILL.md` |
| `skill-creator` | `.github/skills/skill-creator/SKILL.md` |

**Rule:** Whenever a task calls for one of the above skills, READ the SKILL.md before doing
any work. Treat the file contents as binding instructions for that task, exactly as if the
`Skill` tool had loaded it.

## Project Overview

Wine Fermentation System — Python FastAPI backend (4 microservices) + Next.js frontend.

- **Backend:** `src/` — 4 microservices on ports 8000–8003 (fermentation, winery, fruit_origin, analysis_engine)
- **Frontend:** `frontend/` — Turborepo monorepo with Next.js 14 App Router
- **Architecture context:** `.ai-context/project-context.md`
- **ADR index:** `.ai-context/adr/ADR-INDEX.md`

For any architectural decision, read `.github/skills/wine-adr/SKILL.md` before writing an ADR.
For any backend feature, read `.github/skills/wine-backend-dev/SKILL.md` before writing code.
For any frontend feature, read `.github/skills/wine-frontend-context/SKILL.md` before writing code.
