# Fermentation Detail Screen — API Design Guide

## Screen Overview

The fermentation detail screen needs to display:
1. **Current fermentation status** (active, paused, completed, aborted, etc.)
2. **Latest sample values** (temperature, Brix/sugar, pH, dissolved oxygen, etc.)
3. **Active protocol alerts** (threshold violations, missed readings, etc.)

---

## API Calls Required

### 1. GET Fermentation Details (Status)

```
GET /api/fermentations/:fermentationId
```

**Example Response:**
```json
{
  "id": "f-20240918-cabernet-tank4",
  "name": "Cabernet Sauvignon 2024 — Tank 4",
  "variety": "Cabernet Sauvignon",
  "vintage": 2024,
  "tank": { "id": "tank-4", "name": "Tank 4", "capacityLiters": 10000 },
  "status": "active",
  "phase": "primary_fermentation",
  "startedAt": "2024-09-18T08:00:00Z",
  "estimatedCompletionAt": "2024-09-28T08:00:00Z",
  "completedAt": null,
  "protocolId": "prot-cabernet-standard-v2",
  "protocolName": "Cabernet Standard V2",
  "winemaker": { "id": "user-42", "name": "Elena Rossi" },
  "notes": "Grapes from north block, slightly higher sugar than average."
}
```

---

### 2. GET Latest Sample Values

```
GET /api/fermentations/:fermentationId/samples/latest
```

**Example Response:**
```json
{
  "fermentationId": "f-20240918-cabernet-tank4",
  "sampledAt": "2024-09-20T09:00:00Z",
  "readings": {
    "temperature":        { "value": 24.5, "unit": "°C",    "status": "normal" },
    "brix":               { "value": 14.2, "unit": "°Bx",   "status": "normal" },
    "ph":                 { "value": 3.45, "unit": "pH",     "status": "normal" },
    "titratable_acidity": { "value": 6.2,  "unit": "g/L",   "status": "normal" },
    "dissolved_oxygen":   { "value": 0.18, "unit": "mg/L",  "status": "warning" },
    "volatile_acidity":   { "value": 0.32, "unit": "g/L",   "status": "normal" },
    "alcohol_estimate":   { "value": 8.1,  "unit": "%ABV",  "status": "normal" }
  },
  "sampleId": "smp-20240920-0900"
}
```

---

### 3. GET Active Protocol Alerts

```
GET /api/fermentations/:fermentationId/alerts?status=active
```

**Example Response:**
```json
{
  "fermentationId": "f-20240918-cabernet-tank4",
  "total": 2,
  "alerts": [
    {
      "id": "alert-881",
      "type": "threshold_violation",
      "severity": "warning",
      "parameter": "dissolved_oxygen",
      "message": "Dissolved oxygen is elevated above protocol threshold.",
      "thresholdValue": 0.15,
      "actualValue": 0.18,
      "triggeredAt": "2024-09-20T09:00:00Z",
      "status": "active",
      "recommendedAction": "Check pump seal and reduce micro-oxygenation rate."
    }
  ]
}
```

---

## Summary

| Purpose | Method | Endpoint |
|---|---|---|
| Status & metadata | `GET` | `/api/fermentations/:id` |
| Latest sample readings | `GET` | `/api/fermentations/:id/samples/latest` |
| Active protocol alerts | `GET` | `/api/fermentations/:id/alerts?status=active` |

All three calls can be made **in parallel** on component mount. Add a polling interval (e.g., 60s) on samples and alerts for near-real-time monitoring.
