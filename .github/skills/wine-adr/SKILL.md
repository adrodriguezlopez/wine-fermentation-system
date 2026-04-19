---
name: wine-adr
description: >
  Use when working on the Wine Fermentation System and the task involves a design decision,
  new module, new entity with non-obvious design choices, cross-module impact, schema decisions,
  or anything where the "why" needs to be recorded. Triggers on: "should we write an ADR",
  "architectural decision", "design decision", "before implementing", "new module", "how should
  we model X", "what approach for Y". Also use when the user asks to write, create, or update
  an ADR in this project. Don't wait for explicit mention of "ADR" — if a design decision is
  being made, this skill applies.
---

# Wine Fermentation System — ADR Skill

ADRs (Architecture Decision Records) are the project's "why" record. Every significant
implementation in this codebase is preceded by an ADR. They prevent schema regret, surface
cross-module conflicts before code is written, and give future sessions the context they need.

---

## When an ADR is required vs optional

**Required — write ADR before touching code:**
- New module
- New entity with non-obvious design (relationships, tenancy scoping, delete strategy)
- Decision that touches multiple modules
- Schema changes that are hard to undo (new table, new FK, column type choice)
- Any design where alternatives exist and the choice needs justification

**Optional — ADR can follow or be skipped:**
- Adding a field to an existing entity following established patterns
- Bug fix
- Implementing something already fully specified by an existing ADR
- Refactor that doesn't change the public interface

**When in doubt: write the ADR.** It takes 30 minutes and prevents hours of rework.

---

## Step 1 — Check for an existing ADR first

Before creating a new ADR, read:
```
/.ai-context/adr/ADR-INDEX.md
/.ai-context/adr/ADR-PENDING-GUIDE.md
```

Check if:
- An ADR already covers this decision (link to it instead of duplicating)
- An existing ADR needs to be superseded (update its status + create new one)
- Related ADRs exist that must be cross-referenced

---

## Step 2 — Determine the next ADR number

Check the last entry in `ADR-INDEX.md` to get the next available number.
**Never assume the number** — always read the index. Two concurrent sessions will otherwise
create duplicate-numbered ADRs.

---

## Step 3 — Choose the right template

Read `/.ai-context/adr/ADR-template-selection-guide.md` to decide between:
- **Light** (`ADR-template-light.md`) — simple/scoped decisions, ~70% of ADRs
- **Full** (`ADR-template.md`) — new modules, multi-module impact, complex APIs, ~30%

Then read **1-2 real ADRs as quality reference** before writing — they show the actual standard better than the template:
- **ADR-041** — example with detailed schema in Decision
- **ADR-040** — example with code and multi-layer architecture
- **ADR-038** — example of a well-structured technical ADR

## Step 4 — Write the ADR

File path: `/.ai-context/adr/ADR-<NNN>-<short-kebab-title>.md`

Every ADR in this project must answer:
- **Multi-tenancy**: how is `winery_id` scoping handled?
- **Layer placement**: which module/service owns this?
- **Cross-module impact**: which existing ADRs does this touch?

Required sections (both templates):
- `Status`, `Context`, `Decision`, `Consequences`, `Related ADRs`

The `Related ADRs` section is **mandatory** — every ADR in this project cross-references related decisions. Even if there are no direct dependencies, note the closest related ADRs.

---

## Step 5 — Update ADR-INDEX.md

Add a row to the summary table in `/.ai-context/adr/ADR-INDEX.md`:

```markdown
| **[ADR-NNN](./ADR-NNN-title.md)** | Short Title | Proposed | YYYY-MM-DD | High/Medium/Low |
```

Status lifecycle:
- `Proposed` — written, not yet approved
- `Accepted` — decision confirmed, ready to implement
- `✅ Implemented` — code complete, tests passing

---

## Step 6 — Link from the affected module's context

Update `src/modules/<module>/.ai-context/module-context.md` to reference the new ADR.
Find the ADR references section (or add one) and link it:

```markdown
### Governing ADRs
- [ADR-NNN: Title](../../../../.ai-context/adr/ADR-NNN-title.md)
```

---

## Step 7 — Stop. Don't implement yet.

After the ADR is written and the index is updated, **stop and tell the developer**:

> "ADR-NNN is written and added to the index. Review and confirm the decision before I start
> implementing. Use the `wine-backend-dev` skill when ready to proceed."

The ADR is the design phase. Implementation is a separate session.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Assuming the next ADR number | Always read ADR-INDEX.md first (Step 2) |
| Using wrong template | Read selection guide first (Step 3) |
| Not reading real ADRs before writing | ADR-040/041/038 show the quality bar (Step 3) |
| Missing Related ADRs section | It's mandatory in both templates (Step 4) |
| Writing ADR but not updating the index | Step 5 is mandatory |
| Writing ADR but not linking from module-context | Step 6 is mandatory |
| Starting implementation in the same response | Stop after Step 7 |
| Skipping the ADR for "small" entities | If schema is involved, write it |
| Inventing new conventions | Read ARCHITECTURAL_GUIDELINES.md first |
