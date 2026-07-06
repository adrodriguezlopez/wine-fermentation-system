---
name: wine-frontend-context
description: >
  Frontend integration context for the Wine Fermentation System. Use when the user needs to
  know what backend APIs, auth flows, domain entities, or product constraints the frontend must
  work with. Also use when comparing UI needs against the current backend surface, or when a
  request asks what data or endpoints exist for fermentations, protocols, alerts, analyses,
  wineries, vineyards, or harvest lots.
when_to_use: >
  Trigger for questions about API responses, auth/session behavior, domain concepts shown in the UI,
  multi-tenancy, polling constraints, user roles, screen planning, or backend/frontend alignment.
---

# Wine Fermentation System — Frontend Context

Use this skill to answer: what the backend already provides, what the frontend must reflect,
and which product/domain constraints are non-negotiable.

This skill is context, not implementation detail. For coding patterns in the existing Next.js app,
also use `wine-frontend-dev`.

## What This Skill Covers

- authentication and user-role context relevant to frontend work
- backend endpoint availability by module
- domain concepts the UI must represent correctly
- UX constraints such as polling, tenancy boundaries, and role-based behavior

## What This Skill Does Not Cover

- detailed React implementation patterns
- where files belong in `frontend/apps/web`
- how to structure client/server components
- form libraries, testing setup, or TanStack Query code style

Those belong in `wine-frontend-dev`.

## Read The Right Reference

- `system-overview-and-auth.md` — backend shape, auth flow, roles, and tenancy assumptions
- `endpoint-reference.md` — module-by-module endpoint inventory relevant to frontend integration
- `domain-and-ux-constraints.md` — domain language, screen planning inputs, polling rules, and UI constraints

## Current Reality

- The backend is broad and mostly ready for frontend integration.
- The frontend is partially scaffolded, not empty.
- The frontend should be designed around the backend that exists today, not around guessed endpoints.
- Some backend behaviors have special constraints, such as historical endpoints using a different auth header pattern.

## Working Rules

1. Start from backend reality, not screen mockups alone.
2. Distinguish clearly between:
   - endpoint exists
   - endpoint shape is inferred
   - frontend flow is still a proposal
3. When a user asks whether a screen or interaction is possible, verify it against the endpoint reference first.
4. When a user asks how to build it in code, switch from this skill to `wine-frontend-dev` after grounding the requirements.
5. Keep this skill focused on domain/API truth, not implementation recipes.

## Maintenance Rule

If backend APIs change, update the smallest relevant reference file instead of growing this overview.

Keep `SKILL.md` as:

- discovery metadata
- context boundaries
- navigation to references

Push detailed truth into the reference files.