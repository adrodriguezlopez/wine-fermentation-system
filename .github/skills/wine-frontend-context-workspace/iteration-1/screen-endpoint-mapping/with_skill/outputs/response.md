# Wine Fermentation System — Screen-to-Endpoint Mapping

> **Mobile-first constraint applies to every screen listed below.** Winemakers use these screens
> in the field on phones. Design for small viewports first; promote to larger layouts progressively.
> All endpoints require `Authorization: Bearer <access_token>` unless noted as public.

---

## 1. `/login` — Login Screen (Public)

The only public screen. Collects credentials, stores tokens, then redirects to the dashboard.

| Action | Endpoint |
|--------|----------|
| Submit login form | `POST /api/v1/auth/login` |
| Load current user + role after login | `GET /api/v1/auth/me` |
| Auto-refresh expired access token | `POST /api/v1/auth/refresh` |

**Notes:**
- Store `access_token` in memory only (not localStorage).
- Store `refresh_token` in an httpOnly cookie or secure storage.
- On 401 anywhere in the app, call `/auth/refresh` and retry once; on failure redirect here.
- The `role` field from `/auth/me` (`WINEMAKER` | `ADMIN`) drives all role-based UI gates.

---

## 2. `/dashboard` — Active Fermentations Overview

The landing screen after login. Shows all active fermentations for the user's winery, their
status, and the latest reading for each. **Poll every 30–60 seconds** while any fermentation
is `ACTIVE`, `SLOW`, or `STUCK`; stop polling individual entries when status is `COMPLETED`.

| Purpose | Endpoint |
|---------|----------|
| Fermentation list (paginated) | `GET /api/v1/fermentations` |
| Latest sample for each active card | `GET /api/v1/fermentations/{id}/samples/latest` *(poll 30–60 s)* |
| Status distribution (donut chart data) | derived from `GET /api/v1/fermentations` |
| Alert badge count per card | `GET /api/v1/executions/{id}/alerts` *(poll 30–60 s)* |
| Create new fermentation | `POST /api/v1/fermentations` |
| Create fermentation with blend | `POST /api/v1/fermentations/blends` |

**Notes:**
- `GET /api/v1/fermentations` returns paginated `{ items, total, page, size, pages }`.
- The alert badge poll only applies to fermentations that have an active protocol execution.

---

## 3. `/fermentations` — Fermentation List View

Full list with filtering, search, and historical access.

| Purpose | Endpoint |
|---------|----------|
| Paginated list | `GET /api/v1/fermentations` |
| Historical fermentations list | `GET /api/v1/fermentation/historical` ⚠️ |
| Import job list (historical) | `GET /api/v1/fermentation/historical/import` ⚠️ |

> ⚠️ **`X-Winery-ID` header required.** Historical endpoints do **not** extract the winery from
> the JWT. You must explicitly set `X-Winery-ID: <winery_id>` on every request to:
> - `GET /api/v1/fermentation/historical`
> - `GET /api/v1/fermentation/historical/{id}`
> - `GET /api/v1/fermentation/historical/{id}/samples`
> - `GET /api/v1/fermentation/historical/import`
>
> The `winery_id` value comes from `/auth/me`. Build a separate Axios instance (or fetch
> wrapper) that automatically attaches this header for all historical requests.

---

## 4. `/fermentations/:id` — Fermentation Detail View

The richest screen. Combines the sample time-series chart, timeline, alerts panel, analysis
results, and quick-action entry. **Poll `samples/latest` every 30–60 s** while active.

### 4a. Core data

| Purpose | Endpoint |
|---------|----------|
| Fermentation record | `GET /api/v1/fermentations/{id}` |
| All samples (chart data) | `GET /api/v1/fermentations/{id}/samples` |
| Latest sample (live value, polled) | `GET /api/v1/fermentations/{id}/samples/latest` *(poll)* |
| Full event timeline | `GET /api/v1/fermentations/{id}/timeline` |
| Computed statistics | `GET /api/v1/fermentations/{id}/statistics` |
| Validation state | `GET /api/v1/fermentations/{id}/validation` |
| Available sample types | `GET /api/v1/samples/types` |
| Record new sample | `POST /api/v1/fermentations/{id}/samples` |
| Update fermentation metadata | `PATCH /api/v1/fermentations/{id}` |
| Change status | `PATCH /api/v1/fermentations/{id}/status` |
| Mark complete | `POST /api/v1/fermentations/{id}/complete` |

### 4b. Anomaly / recommendation flow (Analysis Engine — port 8003)

After the winemaker records a sample, trigger analysis immediately to check for anomalies.

| Purpose | Endpoint |
|---------|----------|
| Trigger analysis after new sample | `POST /api/v1/analyses` |
| Poll for analysis result | `GET /api/v1/analyses/{id}` |
| List all analyses for this fermentation | `GET /api/v1/analyses/fermentation/{id}` |
| Get a specific recommendation | `GET /api/v1/recommendations/{id}` |
| Apply a recommendation | `PUT /api/v1/recommendations/{id}/apply` |
| List protocol advisories | `GET /api/v1/fermentations/{id}/advisories` |
| Acknowledge an advisory | `POST /api/v1/advisories/{id}/acknowledge` |

**Anomaly/recommendation UI flow:**
1. Winemaker taps "Record Sample" → `POST /api/v1/fermentations/{id}/samples`
2. Immediately call `POST /api/v1/analyses` to trigger analysis.
3. Poll `GET /api/v1/analyses/{id}` until result is ready (or show a spinner).
4. If anomalies detected, overlay markers on the sample timeline chart.
5. If recommendations exist, surface them as action cards with an "Apply" button
   (`PUT /api/v1/recommendations/{id}/apply`).
6. Separately, show advisories from `GET /api/v1/fermentations/{id}/advisories` as a
   compliance panel; each advisory has an "Acknowledge" button
   (`POST /api/v1/advisories/{id}/acknowledge`).

### 4c. Historical detail (when viewing an archived fermentation)

| Purpose | Endpoint |
|---------|----------|
| Historical fermentation record | `GET /api/v1/fermentation/historical/{id}` ⚠️ |
| Historical samples | `GET /api/v1/fermentation/historical/{id}/samples` ⚠️ |

> ⚠️ Both require `X-Winery-ID` header (see §3 above).

---

## 5. `/fermentations/:id/samples` — Sample Recording Screen

Focused mobile form for recording a new measurement in the field.

| Purpose | Endpoint |
|---------|----------|
| Available sample types (form schema) | `GET /api/v1/samples/types` |
| Submit new sample | `POST /api/v1/fermentations/{id}/samples` |
| Confirm latest after submission | `GET /api/v1/fermentations/{id}/samples/latest` |
| Trigger post-sample analysis | `POST /api/v1/analyses` |

**Mobile-first note:** This screen must work on a slow connection. Consider optimistic UI —
show the sample as "pending" locally and sync when connectivity returns.

---

## 6. `/fermentations/:id/protocol` — Protocol Execution Tracker

Tracks which steps of a running protocol have been completed and surfaces alerts for
overdue or skipped steps.

| Purpose | Endpoint |
|---------|----------|
| Start executing a protocol on this fermentation | `POST /api/v1/fermentations/{id}/execute` |
| Get execution status | `GET /api/v1/executions/{id}` |
| List all executions | `GET /api/v1/executions` |
| Update execution | `PATCH /api/v1/executions/{id}` |
| Complete a step | `POST /api/v1/executions/{id}/complete` |
| List step completions | `GET /api/v1/executions/{id}/completions` |
| Get completion detail | `GET /api/v1/completions/{id}` |
| List alerts for this execution (polled) | `GET /api/v1/executions/{id}/alerts` *(poll 30–60 s)* |
| Acknowledge an alert | `POST /api/v1/alerts/{id}/acknowledge` |
| Dismiss an alert | `POST /api/v1/alerts/{id}/dismiss` |
| Actions taken during this execution | `GET /api/v1/executions/{id}/actions` |

**Alert UI — two distinct buttons are required:**
- **Acknowledge** (`POST /api/v1/alerts/{id}/acknowledge`) — marks alert as seen; it remains
  visible but greyed out. Use label "Mark as seen" or similar.
- **Dismiss** (`POST /api/v1/alerts/{id}/dismiss`) — removes alert from the active list
  entirely. Use label "Dismiss" or "Resolved".

These are not interchangeable. Do not collapse them into a single action.

---

## 7. `/fermentations/:id/actions` — Winemaker Action Log

Records and displays interventions the winemaker has made (additions, adjustments, etc.).

| Purpose | Endpoint |
|---------|----------|
| List actions for this fermentation | `GET /api/v1/fermentations/{id}/actions` |
| Record a new action | `POST /api/v1/fermentations/{id}/actions` |
| Get action detail | `GET /api/v1/actions/{id}` |
| Update action outcome | `PATCH /api/v1/actions/{id}/outcome` |
| Delete action (ADMIN only) | `DELETE /api/v1/actions/{id}` |

---

## 8. `/protocols` — Protocol Template List

Manage reusable protocol templates (recipes).

| Purpose | Endpoint |
|---------|----------|
| List protocols | `GET /api/v1/protocols` |
| Create new protocol | `POST /api/v1/protocols` |
| Clone an existing protocol | `POST /api/v1/protocols/{id}/clone` |
| Delete protocol | `DELETE /api/v1/protocols/{id}` |

---

## 9. `/protocols/:id` — Protocol Editor

Step-by-step editor for a single protocol template.

| Purpose | Endpoint |
|---------|----------|
| Load protocol | `GET /api/v1/protocols/{id}` |
| Update protocol metadata | `PATCH /api/v1/protocols/{id}` |
| List steps | `GET /api/v1/protocols/{id}/steps` |
| Add a step | `POST /api/v1/protocols/{id}/steps` |
| Update a step | `PATCH /api/v1/protocols/{id}/steps/{sid}` |
| Delete a step | `DELETE /api/v1/protocols/{id}/steps/{sid}` |
| Clone this protocol | `POST /api/v1/protocols/{id}/clone` |

---

## 10. `/analysis/:id` — Analysis Result View

Deep-dive view for a single analysis run, showing anomalies, recommendations, and advisories.

| Purpose | Endpoint |
|---------|----------|
| Analysis result | `GET /api/v1/analyses/{id}` |
| All analyses for the parent fermentation | `GET /api/v1/analyses/fermentation/{id}` |
| Recommendation detail | `GET /api/v1/recommendations/{id}` |
| Apply recommendation | `PUT /api/v1/recommendations/{id}/apply` |
| Protocol advisories | `GET /api/v1/fermentations/{id}/advisories` |
| Acknowledge advisory | `POST /api/v1/advisories/{id}/acknowledge` |

---

## 11. `/vineyards` — Vineyard Management

| Purpose | Endpoint |
|---------|----------|
| List vineyards | `GET /api/v1/vineyards/` |
| Create vineyard | `POST /api/v1/vineyards/` |
| Update vineyard | `PATCH /api/v1/vineyards/{id}` |
| Delete vineyard | `DELETE /api/v1/vineyards/{id}` |

---

## 12. `/harvest-lots` — Harvest Lot Tracking

| Purpose | Endpoint |
|---------|----------|
| List harvest lots | `GET /api/v1/harvest-lots/` |
| Create harvest lot | `POST /api/v1/harvest-lots/` |
| Get harvest lot | `GET /api/v1/harvest-lots/{id}` |
| Update harvest lot | `PATCH /api/v1/harvest-lots/{id}` |
| Delete harvest lot | `DELETE /api/v1/harvest-lots/{id}` |

---

## 13. `/admin/wineries` — Admin: Winery Management (ADMIN role only)

Hide this entire section from `WINEMAKER` users. Gate in the UI using the `role` field from
`GET /api/v1/auth/me`.

| Purpose | Endpoint |
|---------|----------|
| List all wineries | `GET /api/v1/admin/wineries` |
| Create winery | `POST /api/v1/admin/wineries` |
| Get winery by ID | `GET /api/v1/admin/wineries/{id}` |
| Get winery by code | `GET /api/v1/admin/wineries/code/{code}` |
| Update winery | `PATCH /api/v1/admin/wineries/{id}` |
| Delete winery | `DELETE /api/v1/admin/wineries/{id}` |

---

## Cross-cutting concerns summary

### `X-Winery-ID` header — historical endpoints only

The following four endpoints use `X-Winery-ID: <winery_id>` instead of extracting winery
from the JWT. Set up a dedicated HTTP client instance for these:

| Endpoint |
|----------|
| `GET /api/v1/fermentation/historical` |
| `GET /api/v1/fermentation/historical/{id}` |
| `GET /api/v1/fermentation/historical/{id}/samples` |
| `GET /api/v1/fermentation/historical/import` |

Read `winery_id` from the `/auth/me` response and attach it automatically in this client.

### Polling targets (30–60 s interval, stop when `COMPLETED`)

| Endpoint | Screen |
|----------|--------|
| `GET /api/v1/fermentations` | Dashboard |
| `GET /api/v1/fermentations/{id}/samples/latest` | Dashboard cards, Detail view |
| `GET /api/v1/executions/{id}/alerts` | Dashboard badge, Protocol tracker |

### Analysis engine endpoints for anomaly/recommendation flow

All live at port 8003 (or the same Nginx host in staging/prod):

| Endpoint | When to call |
|----------|-------------|
| `POST /api/v1/analyses` | Immediately after recording a sample |
| `GET /api/v1/analyses/{id}` | Poll until result ready |
| `GET /api/v1/analyses/fermentation/{id}` | Load history on detail screen |
| `GET /api/v1/recommendations/{id}` | When analysis returns recommendation IDs |
| `PUT /api/v1/recommendations/{id}/apply` | Winemaker taps "Apply" on a recommendation |
| `GET /api/v1/fermentations/{id}/advisories` | Load alongside analysis results |
| `POST /api/v1/advisories/{id}/acknowledge` | Winemaker taps "Acknowledge" on advisory |

### Mobile-first constraint

All screens must be designed for small phone viewports first. Key implications:
- Sample recording form (`/fermentations/:id/samples`) is the most frequently used mobile action — keep it to a single tap-friendly form.
- Alert acknowledge/dismiss buttons must be large enough for thumb targets.
- Dashboard fermentation cards should show status, latest reading, and alert badge at a glance with no horizontal scrolling.
- Charts (sample timeline, status donut) must degrade gracefully to a simplified view on narrow screens.
- Consider optimistic UI for `POST /api/v1/fermentations/{id}/samples` to handle poor field connectivity.
