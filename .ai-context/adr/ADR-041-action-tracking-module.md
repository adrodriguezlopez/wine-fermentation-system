# ADR-041: Action Tracking Module Architecture

**Status:** Accepted  
**Date:** 2026-03-21  
**Authors:** Development Team  
**Related ADRs:** ADR-021 (Protocol Compliance Engine), ADR-035 (Protocol Data Model), ADR-036 (Compliance Scoring), ADR-038 (Deviation Detection), ADR-040 (Alerts)

---

## Context

Winemakers take corrective actions during fermentation in response to anomalies,
missed protocol steps, or analysis recommendations.  These interventions currently
have **no first-class representation** in the system:

- There is no way to record *what was done* when a deviation or alert occurs.
- The compliance engine cannot distinguish "step missed" from "step missed, then
  corrective action applied".
- The analysis engine's `RecommendationService` generates suggestions but has no
  feedback loop — it never learns whether a recommendation was followed and what
  the outcome was.
- Winery managers cannot audit corrective interventions for regulatory or
  operational-review purposes.

ADR-022 (originally scoped in the pending-guide) deferred action tracking to the
"post-MVP" backlog.  With protocol compliance (ADR-035/036), deviation detection
(ADR-038), and automated alerts (ADR-040) all complete, the feedback channel is the
only remaining structural gap in the Protocol Compliance Engine.

---

## Decision

### 1. Domain Entities

#### `WinemakerAction`  (new table `winemaker_actions`)
Records a single corrective or proactive action taken by a winemaker.

```
winemaker_actions
─────────────────────────────────────────────────────────────────────
id                  SERIAL PK
winery_id           INT FK wineries.id          (multi-tenancy)
fermentation_id     INT FK fermentations.id      (nullable — some actions are protocol-level)
execution_id        INT FK protocol_executions.id (nullable)
step_id             INT FK protocol_steps.id      (nullable — action may target a specific step)
alert_id            INT FK protocol_alerts.id     (nullable — action taken in response to alert)
recommendation_id   INT FK analysis_results.id    (nullable — from RecommendationService)

action_type         VARCHAR(50) NOT NULL          (enum — see ActionType below)
description         TEXT NOT NULL                 (free text written by winemaker)
taken_at            TIMESTAMP NOT NULL            (when the winemaker reports the action)
taken_by_user_id    INT NOT NULL                  (audit — no FK to avoid cross-module dep)

outcome             VARCHAR(20) DEFAULT 'PENDING' (PENDING | RESOLVED | NO_EFFECT | WORSENED)
outcome_notes       TEXT                          (winemaker's notes after observing result)
outcome_recorded_at TIMESTAMP                     (when outcome was updated)

created_at          TIMESTAMP NOT NULL DEFAULT NOW()
updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
```

#### `ActionType` enum  (stored as VARCHAR in DB)
```
TEMPERATURE_ADJUSTMENT      — cooling/heating intervention
NUTRIENT_ADDITION           — DAP, GoFerm, etc.
SULFUR_ADDITION             — SO2 addition
PUMP_OVER                   — cap management
PUNCH_DOWN                  — cap management
RACK                        — racking to clean vessel
FILTRATION                  — fining / filtration
YEAST_ADDITION              — re-inoculation
H2S_TREATMENT               — copper, aeration
STUCK_FERMENTATION_PROTOCOL — emergency restart
PROTOCOL_STEP_COMPLETED_LATE — late completion recorded
CUSTOM                      — catch-all free-text action
```

#### `ActionOutcome` enum
```
PENDING   — action taken, outcome not yet observed
RESOLVED  — problem resolved after action
NO_EFFECT — action had no measurable effect
WORSENED  — condition deteriorated (triggers new recommendation)
```

---

### 2. Repository Layer

`IActionRepository` (interface):
```
create(action) → WinemakerAction
get_by_id(action_id, winery_id) → Optional[WinemakerAction]
list_by_fermentation(fermentation_id, winery_id, page, page_size) → (List, total)
list_by_execution(execution_id, winery_id, page, page_size) → (List, total)
list_by_alert(alert_id, winery_id) → List[WinemakerAction]
update_outcome(action_id, outcome, outcome_notes) → WinemakerAction
delete(action_id, winery_id) → bool
```

Concrete `ActionRepository` follows the same `AsyncSession`-based pattern as all
other repositories in this module.

---

### 3. Service Layer

#### `ActionService`
Primary orchestration service:
- `record_action(...)` — validate winery ownership of referenced entities, persist
- `update_outcome(...)` — record winemaker's post-action observation
- `get_actions_for_fermentation(...)` — paginated list
- `get_actions_for_execution(...)` — paginated list
- `link_to_alert(action_id, alert_id)` — associate action with alert (auto-acknowledges alert)

**Side-effect on alert acknowledge**: when an action is recorded that references an
`alert_id`, `ProtocolAlertService.acknowledge_alert(alert_id)` is called so the
alert status changes `PENDING → ACKNOWLEDGED` automatically.

#### `ActionEffectivenessService`  (Phase 2 — not MVP)
- `get_effectiveness_summary(winery_id, action_type)` — aggregate RESOLVED/NO_EFFECT/WORSENED counts
- Used by the frontend dashboard and eventually by `RecommendationService` as a
  feedback signal.

---

### 4. API Layer

All endpoints under `/api/v1/fermentations/{fermentation_id}/actions` and a
standalone `/api/v1/actions/{action_id}` for outcome updates.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/fermentations/{ferm_id}/actions` | Record a new action |
| `GET`  | `/api/v1/fermentations/{ferm_id}/actions` | List actions for fermentation |
| `GET`  | `/api/v1/actions/{action_id}` | Get single action |
| `PATCH`| `/api/v1/actions/{action_id}/outcome` | Update outcome after observation |
| `DELETE`| `/api/v1/actions/{action_id}` | Delete (admin only) |
| `GET`  | `/api/v1/executions/{exec_id}/actions` | Actions during a specific execution |

Request / response schemas follow the same `{Entity}CreateRequest` / `{Entity}Response`
Pydantic pattern used by all other fermentation endpoints (ADR-006).

---

### 5. Migration

Alembic migration `007_create_winemaker_actions.py`:
- Creates `winemaker_actions` table with all columns above.
- Indexes: `(winery_id)`, `(fermentation_id)`, `(execution_id)`, `(alert_id)`.
- `down_revision = "006_protocol_template_fields"`.

---

### 6. Scope Decisions

| Topic | Decision |
|-------|----------|
| `recommendation_id` FK | Points to `analysis_results.id` (already exists). Nullable — actions are independent of recommendations. |
| Free text `description` | Required. Winemakers need to express exactly what they did, not just select a type. |
| `ActionType` catalogue | Fixed enum, but `CUSTOM` catch-all preserves flexibility. |
| Outcome tracking | Separate `PATCH /outcome` endpoint — outcome is recorded *after* observation, often hours/days later. |
| `EffectivenessAnalysisService` | Deferred to Phase 2. The schema is designed for it (outcome field) but the analytics layer is not MVP. |
| Cross-module alert auto-acknowledge | `ActionService` calls `ProtocolAlertService.acknowledge_alert()` when `alert_id` is set. Keeps the coupling inside the service layer (not the repository). |
| Learning / feedback loop | Deferred — `ActionEffectivenessService` will feed RESOLVED/NO_EFFECT counts back to `RecommendationTemplateService` in a future ADR. |

---

## Architectural Notes

Following ADR-028 (Module Dependency Management):
- `WinemakerAction` lives in the **fermentation module** (same as `ProtocolAlert`,
  `ProtocolExecution`, etc.) — it is a fermentation domain concept.
- `taken_by_user_id` is stored as a plain integer (no FK to `users`) to avoid a
  cross-module FK dependency, consistent with the pattern in `ProtocolExecution`,
  `StepCompletion`, and `FermentationProtocol`.
- `recommendation_id` references `analysis_results.id` from the analysis-engine
  module — stored as a plain nullable integer for the same reason.

---

## Consequences

- ✅ Closes the feedback loop: winemakers' actions are recorded and linked to the
  alert or deviation that triggered them.
- ✅ Enables future effectiveness analytics without schema changes (outcome field
  is already there).
- ✅ Compliance audit trail: every corrective step is timestamped and attributable
  to a user.
- ✅ Alert auto-acknowledge reduces noise: acting on an alert marks it acknowledged.
- ⚠️ `ActionEffectivenessService` and the feedback loop to `RecommendationService`
  are deliberately deferred — they require enough historical data to be meaningful.
- ❌ No real-time push notifications when an action is recorded by another user
  (out of scope; handled by the alert polling strategy in ADR-040).

---

## Implementation Order

1. **Migration 007** — `winemaker_actions` table
2. **`WinemakerAction` entity** — ORM mapped column, `ActionType` / `ActionOutcome` enums in `step_type.py`
3. **`IActionRepository` + `ActionRepository`** — CRUD + list queries
4. **`ActionService`** — `record_action`, `update_outcome`, `get_actions_for_fermentation`, `link_to_alert`
5. **API schemas** — `ActionCreateRequest`, `ActionOutcomeUpdateRequest`, `ActionResponse`, `ActionListResponse`
6. **`action_router.py`** — 5 endpoints, registered in `main.py`
7. **Unit tests** — `test_action_service.py`, `test_action_api.py` (~20 tests)
