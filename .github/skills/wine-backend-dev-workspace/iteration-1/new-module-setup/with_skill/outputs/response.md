# New Module Setup: `notifications` — With Skill

> **Context read from project files:**
> - `project-context.md`: 4 active modules (fermentation:8000, winery:8001, fruit_origin:8002, analysis_engine:8003). 1,390 tests passing. ADR-040 ("Protocol Notifications & Alerts Strategy") already exists. Next port: **8004**.
> - Templates confirmed in `references/context-templates.md`.

---

Before writing any implementation code, complete all **10 setup steps**:

### Step 1 — Create `src/modules/notifications/.ai-context/module-context.md`
Use Template 1. Key specifics: port 8004, receives anomaly events from Analysis Engine (8003), provides alerts to winemakers. Status: 📋 Planned. Reference: ADR-040.

### Step 2 — Create `src/modules/notifications/.ai-context/domain-model-guide.md`
Use Template 2. Document: `Alert` entity, `AlertRule` entity, `AlertStatus` enum (`PENDING/SENT/FAILED/SUPPRESSED`), `AlertChannel` enum (`IN_APP/EMAIL/PUSH`), `AlertSeverity` enum.

### Step 3 — Add module entry to `/.ai-context/project-context.md`
Use Template 4 under `## System modules`:
```
### Notifications Module
**Status:** 📋 Planned
**Last Updated:** 2026-04-18
**Total Tests:** 0 (not yet implemented)
```

### Step 4 — Add module entry to `/.ai-context/PROJECT_STRUCTURE_MAP.md`
Use Template 6 under `modules/` — all layers marked 📋, 0 tests, port 8004.

### Step 5 — Update `/.ai-context/adr/ADR-INDEX.md`
ADR-040 already exists. Update its row to link it to `src/modules/notifications/`. If scope is broader, write a new ADR before proceeding.

### Step 6 — Create `src/modules/notifications/pyproject.toml`
Copy from `src/modules/analysis_engine/pyproject.toml`. Change: `name = "notifications"`, port references to `8004`.

### Step 7 — Create `src/modules/notifications/Dockerfile`
Copy from `src/modules/analysis_engine/Dockerfile`. Change: module name, port `8003` → `8004`.

### Step 8 — Create `src/modules/notifications/README.md`
One paragraph describing the module.

### Step 9 — Create `src/modules/notifications/tests/conftest.py`
Use the same conftest pattern as other modules.

### Step 10 — Add service block to `docker-compose.yml`
Copy the `analysis_engine` block, adjust name, port 8004, Dockerfile path, healthcheck URL.

---

## Critical design question — resolve before starting

ADR-040 was written for in-protocol notifications inside the fermentation module. You need to decide:

**Is `notifications` a system-wide alert module (consumes all anomaly types from analysis_engine) or a protocol-scoped one (belongs inside fermentation as a new component)?**

Getting this wrong means building in the wrong place. Clarify it first.

---

When all 10 files exist, context and config are ready. Ready to start on domain entities when you give the go-ahead.
