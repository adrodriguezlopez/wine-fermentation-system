# Response: Should We Write an ADR for WinerySettings First?

## Recommendation: Yes, write the ADR first.

Given this project's strong architectural discipline and history, the right call is to **write the ADR before implementing** `WinerySettings`. Here is why, and how to approach it.

---

## Why an ADR First

### 1. The project has a consistent ADR-before-code culture

Looking at the full ADR history (ADR-001 through ADR-041), every significant entity, service, and module has been preceded by an ADR. This is not bureaucracy — the ADRs here are living documents that also record implementation results, test counts, and lessons learned. The `WinerySettings` entity crosses several already-documented concerns and deserves the same treatment.

### 2. WinerySettings touches three existing ADRs

The proposed entity intersects directly with:

- **ADR-016 (Winery Service Layer)** — `WinerySettings` is a child of the `Winery` root entity. Any schema or service changes need to not break the existing 79 winery tests.
- **ADR-040 (Notifications & Alerts)** — Notification preferences are one of the three stated fields. ADR-040 already defines `AlertPreference` (per-user, per-winery). You need to decide: does `WinerySettings` replace, extend, or coexist with `AlertPreference`? This is a significant design question.
- **ADR-025 (Multi-Tenancy Security)** — `WinerySettings` is scoped to a winery. Every query must enforce `winery_id` isolation. The ADR should explicitly record this constraint so future contributors don't miss it.

Without an ADR, these intersections could easily lead to duplication or a schema conflict that requires a costly refactor.

### 3. Key design questions need to be resolved before code

The three feature areas — default protocol, alert thresholds, notification preferences — each raise a specific architectural question:

| Feature | Question to resolve |
|---|---|
| **Default protocol** | Is this a FK to `Protocol`? A string template name? What happens if the referenced protocol is deleted? |
| **Alert thresholds** | Are these per-winery overrides of system defaults, or the only source of truth? Are they stored as a JSON blob or as typed columns? |
| **Notification preferences** | Does this replace or supplement the per-user `AlertPreference` defined in ADR-040? If both exist, which wins? |

Writing a short ADR forces these questions to be answered explicitly and reviewed before any migration is created.

### 4. Database migrations are hard to undo

Once a migration adds a `winery_settings` table (or columns to `wineries`), schema drift becomes a real cost. An ADR surfaces the "store inline on `wineries` vs. separate table" decision and records the rationale, so reviewers can push back before the migration runs.

---

## What the ADR Should Cover

You can keep this ADR short. Use the `ADR-template-light.md` already present in `.ai-context/adr/`. The key decisions to document:

1. **Storage model**: Separate `winery_settings` table (1:1 with `Winery`) vs. JSON column on `wineries` vs. additional columns on `wineries`.
   - A separate table is recommended for clean separation and to avoid bloating the `Winery` entity further (SRP from `ARCHITECTURAL_GUIDELINES.md`).

2. **Relationship to `AlertPreference` (ADR-040)**: Clarify that `WinerySettings` holds *winery-level defaults* while `AlertPreference` holds *per-user overrides*. Document the precedence rule explicitly.

3. **Default protocol field**: Define whether this is a nullable FK to the `protocols` table or a soft reference. Record what happens on protocol deletion.

4. **Alert threshold structure**: Typed columns vs. JSON. Typed columns are preferred for query-ability and validation; JSON is acceptable if thresholds are highly dynamic.

5. **Multi-tenancy enforcement**: Confirm all queries must scope by `winery_id` per ADR-025.

6. **Migration strategy**: One-time migration to seed default settings for existing wineries, or lazy creation on first access.

---

## Suggested ADR Number

The next available number is **ADR-042**. The last recorded ADR in the index is ADR-041 (Action Tracking Module, March 2026).

---

## How Long Will the ADR Take?

Given the project's template and established patterns, a focused ADR for `WinerySettings` should take **2–4 hours** to draft, including the design review. Implementation can begin the same day if the ADR is approved quickly. This is not a gate that meaningfully delays delivery — it is insurance against a redesign after migration.

---

## If You Skip the ADR

The main risks are:

- **Duplication with `AlertPreference`**: Two sources of notification truth with no documented precedence rule.
- **Schema regret**: Inline columns on `wineries` that need to be extracted to a settings table later.
- **Broken winery tests**: ADR-016 tests assume the `Winery` entity shape. Changes without an ADR are more likely to inadvertently break the 79 existing tests.
- **Lost context**: The project's ADR trail is its primary onboarding and audit document. A significant entity with no ADR is an unexplained gap.

---

## Summary

| | Write ADR first | Implement first |
|---|---|---|
| Design questions resolved | Yes | No — discovered during code review |
| Risk of overlap with ADR-040 | Low | High |
| Migration regret risk | Low | Medium–High |
| Time cost | 2–4 hours | 2–4 hours of rework later |
| Consistent with project culture | Yes | No |

**Write ADR-042 first.** It will be short, the template is already there, and it will prevent the two most likely pain points: notification preference duplication and schema drift. Implementation can follow the same day.
