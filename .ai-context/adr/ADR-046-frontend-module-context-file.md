# ADR-046: Frontend Module Context File

**Status:** Proposed  
**Date:** 2026-04-19  
**Authors:** Development Team  
**Related ADRs:** ADR-045 (Frontend Architecture), ADR-007 (Auth Module)

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

Every backend module in `src/modules/<module>/` carries a `.ai-context/module-context.md` file that describes the module's purpose, tech stack, layer structure, and governing ADRs. This file is the primary entry point for Claude Code sessions scoped to that module — without it, a session has no cheap way to discover which ADRs apply or how the module is structured.

The `frontend/` directory (introduced in ADR-045) is treated as a first-class module of the system, but its `.ai-context/module-context.md` does not exist yet. Any Claude Code session working on the frontend currently has to reconstruct this context from scratch by reading the full ADR-045 and the Turborepo workspace files. Creating the file closes this gap.

---

## Decision

1. **Create `frontend/.ai-context/module-context.md`** following the same convention as backend modules (`src/modules/<module>/.ai-context/module-context.md`).

2. **Contents** — the file will document:
   - Module overview and purpose (fermentation monitoring UI)
   - Tech stack: Turborepo + pnpm workspaces, Next.js 14 App Router, TanStack Query v5, Zustand, Shadcn/ui, Tailwind CSS, Vitest + RTL + MSW
   - Workspace structure (`apps/web`, `packages/ui`, `packages/shared`)
   - Architectural constraints (e.g. `winery_id` never in component props, `packages/ui` zero-React rule)
   - Governing ADRs section linking ADR-045 and any other relevant decisions

3. **No new conventions are introduced.** The file follows the same format already used by backend module-context files — structure adapted for a TypeScript/Turborepo workspace rather than a Python module.

4. **File is the only deliverable.** No code, no configuration, no dependency changes are required. This is a documentation-only action.

---

## Consequences

- ✅ Claude Code sessions scoped to `frontend/` immediately find architectural context without having to read full ADR text
- ✅ Consistent documentation convention across all modules (backend and frontend)
- ✅ Governing ADRs section serves as a living index of decisions that affect the frontend
- ⚠️ File must be kept up to date as new frontend ADRs are written — same maintenance burden as backend module-context files
- ❌ Does not replace ADR-045 — both files serve different purposes (ADR = decision record; module-context = session bootstrap reference)

---

## Related ADRs

- **[ADR-045](./ADR-045-frontend-architecture.md)**: Defines the entire frontend architecture that the new module-context file documents; this ADR is the primary governing decision for the frontend module
- **[ADR-007](./ADR-007-auth-module-design.md)**: JWT auth design consumed by the frontend (`winery_id` scoping, `/login` + `/refresh` + `/me` endpoints) — must be referenced in the module-context governing ADRs section

---

## Status
Proposed
