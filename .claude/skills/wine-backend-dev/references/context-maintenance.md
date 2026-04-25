# Context Maintenance Guide

This file tells you **exactly what to update and when** after any backend change.
Both `wine-backend-dev` and `wine-frontend-context` skills reference this guide.

---

## After adding a new entity

| File | What to add |
|------|-------------|
| `/.ai-context/project-context.md` | Add entity to module's component list |
| `/.ai-context/PROJECT_STRUCTURE_MAP.md` | Add to module's entity list with ✅ status |
| `src/modules/<module>/.ai-context/module-context.md` | Add entity + repository + service entries |
| `src/modules/<module>/.ai-context/domain-model-guide.md` | Document entity fields, relationships, rules |
| `.github/skills/wine-frontend-context/SKILL.md` | If it has API endpoints, add them to endpoint tables |

---

## After adding or changing an API endpoint

| File | What to add |
|------|-------------|
| `src/modules/<module>/.ai-context/module-context.md` | Add endpoint to API component list |
| `.github/skills/wine-frontend-context/SKILL.md` | Add endpoint to the correct endpoint table |

---

## After writing or updating tests

| File | What to update |
|------|----------------|
| `/.ai-context/project-context.md` | Update test count for the module (e.g., "728 passing") |
| `src/modules/<module>/.ai-context/module-context.md` | Update "Total Tests" count |

**Rule**: Test count drift causes misaligned expectations across sessions. Update every time.

---

## After creating an Alembic migration

| File | What to add |
|------|-------------|
| `/.ai-context/PROJECT_STRUCTURE_MAP.md` | Note the new migration in alembic/versions |
| `src/modules/<module>/.ai-context/module-context.md` | Reference the migration in the relevant entity section |

---

## After creating a new ADR

| File | What to add |
|------|-------------|
| `/.ai-context/adr/ADR-INDEX.md` | Add entry with ADR number, title, status, date |
| Relevant `module-context.md` | Link to the ADR from the component it governs |
| `.github/skills/wine-backend-dev/SKILL.md` | Only if the ADR changes a system-wide rule |

---

## After completing a module or phase

| File | What to update |
|------|----------------|
| `/.ai-context/project-context.md` | Update module status (e.g., `📋 Proposed → ✅ COMPLETE`) |
| `/.ai-context/PROJECT_STRUCTURE_MAP.md` | Update status icons |

---

## Files at risk of going stale

These files are most commonly out of date — check them when something feels wrong:

1. `/.ai-context/project-context.md` — test counts and module status
2. `.github/skills/wine-frontend-context/SKILL.md` — endpoint tables
3. `src/modules/<module>/.ai-context/module-context.md` — component lists

---

## Quick verification checklist (run after implementing a feature)

- [ ] Test counts in `project-context.md` match `poetry run pytest` output
- [ ] New entity appears in `PROJECT_STRUCTURE_MAP.md`
- [ ] New endpoint appears in `wine-frontend-context/SKILL.md`
- [ ] ADR-INDEX is current if an ADR was created
- [ ] `domain-model-guide.md` reflects the actual entity fields
