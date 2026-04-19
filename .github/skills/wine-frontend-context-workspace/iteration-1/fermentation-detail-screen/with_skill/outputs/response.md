# Building a Fermentation Detail Screen in React

## Screen data requirements

The fermentation detail screen needs three categories of data:
1. **Current status** — the fermentation entity itself
2. **Latest sample values** — the most recent measurement
3. **Active protocol alerts** — alerts on the active protocol execution

---

## API Calls

### 1. Get the fermentation (current status)

```
GET /api/v1/fermentations/{id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 42,
  "name": "Chardonnay Batch 2026-A",
  "status": "ACTIVE",
  "winery_id": 1,
  "created_at": "2026-03-15T08:00:00Z",
  "updated_at": "2026-04-18T10:30:00Z",
  "harvest_lot_id": 7,
  "protocol_execution_id": 15
}
```

Status values: `ACTIVE` | `SLOW` | `STUCK` | `COMPLETED`. The `protocol_execution_id` field is what you need to fetch alerts — it may be `null` if no protocol is running.

---

### 2. Get the latest sample values

```
GET /api/v1/fermentations/{id}/samples/latest
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 301,
  "fermentation_id": 42,
  "sample_type": "FULL_PANEL",
  "recorded_at": "2026-04-18T09:45:00Z",
  "temperature": 18.5,
  "glucose": 42.1,
  "ethanol": 7.3,
  "density": 1.045,
  "ph": 3.4,
  "volatile_acidity": 0.32
}
```

Samples use single-table inheritance — different `sample_type` values return different fields. Always guard for `null` on individual measurement fields.

---

### 3. Get active protocol alerts

Using the `protocol_execution_id` from step 1:

```
GET /api/v1/executions/{execution_id}/alerts
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "items": [
    {
      "id": 88,
      "execution_id": 15,
      "step_id": 4,
      "alert_type": "STEP_OVERDUE",
      "message": "Step 'Add SO2' is 2 hours overdue",
      "severity": "HIGH",
      "created_at": "2026-04-18T08:00:00Z",
      "acknowledged_at": null,
      "dismissed_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

Filter for "active" alerts: `dismissed_at === null`. Acknowledged alerts stay visible but styled grey.

---

## Alert Actions — implement BOTH

- `POST /api/v1/alerts/{id}/acknowledge` — "I've seen this" (stays in list, turns grey)
- `POST /api/v1/alerts/{id}/dismiss` — "I've dealt with this" (removed from active list)

---

## Polling

No WebSockets — poll every 30–60 seconds:
- `GET /api/v1/fermentations/{id}`
- `GET /api/v1/fermentations/{id}/samples/latest`
- `GET /api/v1/executions/{executionId}/alerts` (if execution exists)

Stop polling when `status === "COMPLETED"`.

---

## Summary Table

| # | Endpoint | Purpose | Poll? |
|---|----------|---------|-------|
| 1 | `GET /api/v1/fermentations/{id}` | Status, name, execution ID | Yes |
| 2 | `GET /api/v1/fermentations/{id}/samples/latest` | Latest measurements | Yes |
| 3 | `GET /api/v1/executions/{execution_id}/alerts` | Active protocol alerts | Yes (if execution exists) |
