# Response: WinerySettings Entity — ADR Decision

## Should we write an ADR first?

**Yes — an ADR is required before touching code.**

`WinerySettings` introduces:
- A new entity with non-obvious design choices (1:1 vs embedded columns, JSON vs typed columns, lifecycle coupling)
- A new schema table (`winery_settings`) — hard to undo once deployed
- Cross-module impact: notification preferences and alert thresholds are consumed by the notifications module (ADR-040) and the analysis engine (ADR-020)
- A decision about cross-module FK strategy (protocol reference without DB constraint)

Per the skill rules: *"New entity with non-obvious design (relationships, tenancy scoping, delete strategy)" → ADR required.*

---

## ADR Written: ADR-044

**File:** `/.ai-context/adr/ADR-044-winery-settings-entity.md`

### Summary of decisions made

| Decision | Choice made | Rationale |
|---|---|---|
| Storage model | Separate `winery_settings` table (1:1, `winery_id` as PK+FK) | Keeps `wineries` table stable; avoids wide-table growth |
| Module ownership | `winery` module exclusively | Settings are winery config, not cross-cutting |
| Lifecycle | Auto-created with Winery, never deleted independently | Settings are meaningless without the parent winery |
| `default_protocol_id` | Nullable UUID — no DB-level FK | Avoids cross-module DB coupling (ADR-028 pattern) |
| `alert_thresholds` | JSONB column | Schema flexibility for evolving threshold types |
| API surface | `GET` + `PATCH /admin/wineries/{id}/settings` | Extends ADR-017 namespace and authorization rules |
| Multi-tenancy | `winery_id` from JWT context, same as all other entities | Consistent with ADR-007 |

### Key trade-offs accepted
- ⚠️ `default_protocol_id` integrity enforced at service layer only (no DB FK)
- ⚠️ `alert_thresholds` JSONB requires documented key conventions
- ❌ No per-user overrides within a winery (winery-level granularity only — MVP)

---

## ADR-INDEX.md Updated

Added entry:
```
| ADR-044 | WinerySettings Entity Design | Proposed | 2026-04-19 | Medium |
```

## Module Context Updated

`src/modules/winery/.ai-context/module-context.md` updated with `Governing ADRs` section referencing ADR-044.

---

## Next step

ADR-044 is written and added to the index. Review and confirm the decision before implementing — particularly:
1. Is JSONB acceptable for `alert_thresholds`, or do you prefer a typed column approach?
2. Should `default_protocol_id` have any soft validation on write (check protocol exists via service call)?

Use the `wine-backend-dev` skill when ready to proceed with implementation.
