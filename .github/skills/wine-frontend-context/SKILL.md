---
name: wine-frontend-context
description: >
  Frontend integration context skill for the Wine Fermentation System. USE THIS SKILL whenever
  the user wants to build a frontend, create a UI component, integrate with the API, display
  fermentation data, set up React/Vue/any framework, implement authentication flow, handle API
  calls, design a screen, or discuss the frontend architecture. Also use when comparing what
  the backend provides vs what the UI needs. If the user mentions frontend, UI, dashboard,
  charts, React, components, API integration, tokens, sessions, screens, or "what does the API
  return" — this skill applies. The frontend/ folder is currently empty — this is greenfield work.
---

# Wine Fermentation System — Frontend Context Skill

The backend is a **complete, production-ready REST API**. The frontend is greenfield (the
`frontend/` folder exists but is empty). This skill gives you the full picture of what the
backend exposes so frontend work starts from reality, not guesswork.

---

## System overview for frontend developers

| Concept | Detail |
|---------|--------|
| Architecture | 4 independent microservices behind Nginx reverse proxy |
| API style | REST, JSON, all endpoints under `/api/v1` |
| Auth | JWT Bearer tokens (access + refresh) |
| Multi-tenancy | Every user belongs to one winery; `winery_id` is automatic via JWT |
| Real-time | Polling-based (no WebSockets yet) |
| Target users | Winemakers (field use, mobile-first) + Admins |

---

## Authentication flow

### Login
```
POST /api/v1/auth/login
Body: { "username": "...", "password": "..." }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Refresh
```
POST /api/v1/auth/refresh
Body: { "refresh_token": "..." }
Response: { "access_token": "...", "token_type": "bearer" }
```

### Current user
```
GET /api/v1/auth/me
Header: Authorization: Bearer <token>
Response: { "id": 1, "email": "...", "role": "WINEMAKER|ADMIN", "winery_id": 1 }
```

All other endpoints require `Authorization: Bearer <access_token>`.

### User roles
- **WINEMAKER** — can read/write fermentations, samples, protocols, actions within their winery
- **ADMIN** — can also create/delete wineries, users; has access to admin endpoints

---

## Critical frontend constraints

> **Live data polling:** No WebSockets exist. You MUST poll. Use a 30–60 second interval for:
> - `GET /api/v1/fermentations` (dashboard list)
> - `GET /api/v1/fermentations/{id}/samples/latest` (active fermentation detail)
> - `GET /api/v1/executions/{id}/alerts` (protocol alert badge counts)
>
> Stop polling when fermentation status is `COMPLETED`.

> **Alert lifecycle — two distinct operations:**
> - `POST /alerts/{id}/acknowledge` — marks seen; alert remains in the list (icon turns grey). Use for "I've read this."
> - `POST /alerts/{id}/dismiss` — removes from active list entirely. Use for "I've acted on this."
> Implement BOTH buttons in the alert UI. They are not interchangeable.

---

## Complete API endpoint reference

### Base URL
- Development: `http://localhost:8000` (fermentation), `8001` (winery), `8002` (fruit_origin), `8003` (analysis)
- Staging/Production: Single Nginx entry point, all modules accessible via same host

---

### Fermentation module (port 8000)

#### Fermentations
| Method | Path | Who | Description |
|--------|------|-----|-------------|
| POST | `/api/v1/fermentations` | WINEMAKER | Create fermentation |
| POST | `/api/v1/fermentations/blends` | WINEMAKER | Create fermentation with blend |
| GET | `/api/v1/fermentations` | any | List fermentations (paginated) |
| GET | `/api/v1/fermentations/{id}` | any | Get single fermentation |
| PATCH | `/api/v1/fermentations/{id}` | WINEMAKER | Update fermentation |
| PATCH | `/api/v1/fermentations/{id}/status` | WINEMAKER | Change status |
| POST | `/api/v1/fermentations/{id}/complete` | WINEMAKER | Mark as complete |
| GET | `/api/v1/fermentations/{id}/timeline` | any | Full timeline of events |
| GET | `/api/v1/fermentations/{id}/statistics` | any | Computed statistics |
| GET | `/api/v1/fermentations/{id}/validation` | any | Validation state |

Fermentation status progression: `ACTIVE → SLOW → STUCK → COMPLETED`

#### Samples (measurements)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/samples` | Record a new measurement |
| GET | `/api/v1/fermentations/{id}/samples` | List all samples |
| GET | `/api/v1/fermentations/{id}/samples/latest` | Get most recent sample |
| GET | `/api/v1/fermentations/{id}/samples/{sid}` | Get specific sample |
| GET | `/api/v1/samples/types` | List available sample types |

Sample types use single-table inheritance — each type has different fields.

#### Protocols (winemaker recipe templates)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/protocols` | Create protocol template |
| GET | `/api/v1/protocols` | List protocols |
| GET | `/api/v1/protocols/{id}` | Get protocol |
| PATCH | `/api/v1/protocols/{id}` | Update protocol |
| DELETE | `/api/v1/protocols/{id}` | Delete protocol |
| POST | `/api/v1/protocols/{id}/clone` | Clone protocol |
| POST | `/api/v1/protocols/{id}/steps` | Add step |
| GET | `/api/v1/protocols/{id}/steps` | List steps |
| PATCH | `/api/v1/protocols/{id}/steps/{sid}` | Update step |
| DELETE | `/api/v1/protocols/{id}/steps/{sid}` | Delete step |

#### Protocol execution (tracking a protocol in progress)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/execute` | Start executing a protocol |
| GET | `/api/v1/executions/{id}` | Get execution status |
| PATCH | `/api/v1/executions/{id}` | Update execution |
| GET | `/api/v1/executions` | List executions |
| POST | `/api/v1/executions/{id}/complete` | Complete a protocol step |
| GET | `/api/v1/executions/{id}/completions` | List completions |
| GET | `/api/v1/completions/{id}` | Get completion detail |

#### Alerts (protocol deviation notifications)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/executions/{id}/alerts` | List alerts for an execution |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/api/v1/alerts/{id}/dismiss` | Dismiss alert |

#### Winemaker actions (interventions)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/actions` | Record an action taken |
| GET | `/api/v1/fermentations/{id}/actions` | List actions for fermentation |
| GET | `/api/v1/executions/{id}/actions` | List actions for execution |
| GET | `/api/v1/actions/{id}` | Get action |
| PATCH | `/api/v1/actions/{id}/outcome` | Update action outcome |
| DELETE | `/api/v1/actions/{id}` | Delete action (ADMIN only) |

#### Historical data
| Method | Path | Auth header | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/fermentation/historical` | `X-Winery-ID: <id>` | List historical fermentations |
| GET | `/api/v1/fermentation/historical/{id}` | `X-Winery-ID: <id>` | Get historical fermentation |
| GET | `/api/v1/fermentation/historical/{id}/samples` | `X-Winery-ID: <id>` | Get historical samples |
| GET | `/api/v1/fermentation/historical/import` | `X-Winery-ID: <id>` | List import jobs |

Note: historical endpoints use `X-Winery-ID` header, not JWT winery extraction.

---

### Analysis engine (port 8003)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyses` | Trigger analysis for a fermentation |
| GET | `/api/v1/analyses/{id}` | Get analysis result |
| GET | `/api/v1/analyses/fermentation/{id}` | List analyses for a fermentation |
| GET | `/api/v1/recommendations/{id}` | Get recommendation |
| PUT | `/api/v1/recommendations/{id}/apply` | Apply a recommendation |
| GET | `/api/v1/fermentations/{id}/advisories` | List protocol advisories |
| POST | `/api/v1/advisories/{id}/acknowledge` | Acknowledge advisory |

---

### Winery module (port 8001)

| Method | Path | Who | Description |
|--------|------|-----|-------------|
| POST | `/api/v1/admin/wineries` | ADMIN | Create winery |
| GET | `/api/v1/admin/wineries` | ADMIN | List all wineries |
| GET | `/api/v1/admin/wineries/{id}` | any | Get winery |
| GET | `/api/v1/admin/wineries/code/{code}` | any | Get winery by code |
| PATCH | `/api/v1/admin/wineries/{id}` | any | Update winery |
| DELETE | `/api/v1/admin/wineries/{id}` | ADMIN | Delete winery |

---

### Fruit origin module (port 8002)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/vineyards/` | Create vineyard |
| GET | `/api/v1/vineyards/` | List vineyards |
| GET | `/api/v1/vineyards/{id}` | Get vineyard |
| PATCH | `/api/v1/vineyards/{id}` | Update vineyard |
| DELETE | `/api/v1/vineyards/{id}` | Delete vineyard |
| POST | `/api/v1/harvest-lots/` | Create harvest lot |
| GET | `/api/v1/harvest-lots/` | List harvest lots |
| GET | `/api/v1/harvest-lots/{id}` | Get harvest lot |
| PATCH | `/api/v1/harvest-lots/{id}` | Update harvest lot |
| DELETE | `/api/v1/harvest-lots/{id}` | Delete harvest lot |

---

## Key domain concepts for UI design

### Fermentation lifecycle
A fermentation represents one batch of wine being produced. It has:
- Status: `ACTIVE → SLOW → STUCK → COMPLETED`
- Multiple **samples** (time-series measurements: temperature, glucose, ethanol, density...)
- An optional **protocol execution** (step-by-step process being followed)
- **Actions** logged by the winemaker (interventions made)
- **Alerts** when protocol deviates
- **Analyses** generated by the analysis engine (anomaly detection)

### Protocol system
A **Protocol** is a template (recipe). A **ProtocolExecution** is an instance of that template
applied to a specific fermentation. **StepCompletions** track which steps were done.
**ProtocolAlerts** fire when steps are overdue or skipped.

### Analysis engine
After a sample is recorded, an analysis can be triggered. It returns:
- Detected **anomalies** (deviations from expected patterns)
- **Recommendations** (suggested actions to take)
- **Advisories** (protocol compliance issues)

### Multi-tenancy in the UI
Every user belongs to exactly one winery. The JWT carries `winery_id`. The frontend never
needs to pass winery_id explicitly to POST/PATCH/DELETE — the backend reads it from the token.
GET list endpoints will automatically scope results to the user's winery.

---

## Frontend architecture recommendations

### Suggested screen map

```
/login                          Public
/dashboard                      Active fermentations overview
/fermentations                  List view
/fermentations/:id              Detail view (samples chart, timeline, alerts)
/fermentations/:id/samples      Sample recording
/fermentations/:id/protocol     Protocol execution tracker
/fermentations/:id/actions      Action log
/protocols                      Protocol template management
/protocols/:id                  Protocol editor (steps)
/analysis/:id                   Analysis result view
/vineyards                      Vineyard management
/harvest-lots                   Harvest lot tracking
/admin/wineries                 Admin only
```

### API integration guide

For the API client layer, use standard fetch with interceptors — or a library like Axios.
All responses follow RFC 7807 error format on failures:
```json
{
  "type": "...",
  "title": "...",
  "status": 422,
  "detail": "..."
}
```

Token strategy:
1. Store `access_token` in memory (not localStorage for security)
2. Store `refresh_token` in an httpOnly cookie or secure storage
3. On 401, auto-call `/auth/refresh` and retry once
4. On refresh failure, redirect to `/login`

### Pagination pattern
List endpoints return:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### Charts / data visualization
Fermentation monitoring is data-heavy. Key charts needed:
- **Sample timeline**: multi-line chart of temperature, glucose, ethanol, density over time
- **Status distribution**: donut chart of active fermentations by status
- **Protocol compliance**: progress bar per execution (steps completed / total)
- **Anomaly markers**: overlay on the sample timeline showing where anomalies were detected

---

## Important constraints for frontend

1. **Mobile-first** — winemakers are in the field with phones; design for small screens first
2. **Real-time polling** — no WebSockets; poll active fermentations every 30–60s
3. **Role-based UI** — hide admin actions from WINEMAKER role users; check `role` from `/auth/me`
4. **Offline consideration** — winemakers may have poor connectivity; consider optimistic UI
5. **Historical data** uses a different auth pattern (`X-Winery-ID` header) — handle separately

---

## Updating this skill

When new API endpoints are added to the backend, update this skill's endpoint tables.
When the domain model changes (new entity, new status), update the **Key domain concepts** section.
Reference: `/.ai-context/project-context.md` for current implementation status of each module.
