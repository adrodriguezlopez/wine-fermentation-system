# Endpoint Reference

Use this file to answer whether the backend already exposes the data a frontend flow needs.

## Base URLs

- Development: ports `8000` (fermentation), `8001` (winery), `8002` (fruit origin), `8003` (analysis)
- Staging/production: typically exposed behind a single entry point

## Fermentation Module

### Fermentations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations` | Create fermentation |
| POST | `/api/v1/fermentations/blends` | Create fermentation with blend |
| GET | `/api/v1/fermentations` | List fermentations |
| GET | `/api/v1/fermentations/{id}` | Get fermentation |
| PATCH | `/api/v1/fermentations/{id}` | Update fermentation |
| PATCH | `/api/v1/fermentations/{id}/status` | Change status |
| POST | `/api/v1/fermentations/{id}/complete` | Mark as complete |
| GET | `/api/v1/fermentations/{id}/timeline` | Timeline of events |
| GET | `/api/v1/fermentations/{id}/statistics` | Computed stats |
| GET | `/api/v1/fermentations/{id}/validation` | Validation state |

### Samples

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/samples` | Record sample |
| GET | `/api/v1/fermentations/{id}/samples` | List samples |
| GET | `/api/v1/fermentations/{id}/samples/latest` | Latest sample |
| GET | `/api/v1/fermentations/{id}/samples/{sid}` | Sample detail |
| GET | `/api/v1/samples/types` | Available sample types |

### Protocol Templates

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/protocols` | Create protocol |
| GET | `/api/v1/protocols` | List protocols |
| GET | `/api/v1/protocols/{id}` | Get protocol |
| PATCH | `/api/v1/protocols/{id}` | Update protocol |
| DELETE | `/api/v1/protocols/{id}` | Delete protocol |
| POST | `/api/v1/protocols/{id}/clone` | Clone protocol |
| POST | `/api/v1/protocols/{id}/steps` | Add step |
| GET | `/api/v1/protocols/{id}/steps` | List steps |
| PATCH | `/api/v1/protocols/{id}/steps/{sid}` | Update step |
| DELETE | `/api/v1/protocols/{id}/steps/{sid}` | Delete step |

### Protocol Execution

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/execute` | Start protocol execution |
| GET | `/api/v1/executions/{id}` | Execution status |
| PATCH | `/api/v1/executions/{id}` | Update execution |
| GET | `/api/v1/executions` | List executions |
| POST | `/api/v1/executions/{id}/complete` | Complete protocol step |
| GET | `/api/v1/executions/{id}/completions` | List completions |
| GET | `/api/v1/completions/{id}` | Completion detail |

### Alerts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/executions/{id}/alerts` | List alerts |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/api/v1/alerts/{id}/dismiss` | Dismiss alert |

### Winemaker Actions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fermentations/{id}/actions` | Record action |
| GET | `/api/v1/fermentations/{id}/actions` | List fermentation actions |
| GET | `/api/v1/executions/{id}/actions` | List execution actions |
| GET | `/api/v1/actions/{id}` | Get action |
| PATCH | `/api/v1/actions/{id}/outcome` | Update action outcome |
| DELETE | `/api/v1/actions/{id}` | Delete action |

### Historical Fermentation Data

| Method | Path | Special note |
|--------|------|--------------|
| GET | `/api/v1/fermentation/historical` | Uses `X-Winery-ID` header |
| GET | `/api/v1/fermentation/historical/{id}` | Uses `X-Winery-ID` header |
| GET | `/api/v1/fermentation/historical/{id}/samples` | Uses `X-Winery-ID` header |
| GET | `/api/v1/fermentation/historical/import` | Uses `X-Winery-ID` header |

## Analysis Engine

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyses` | Trigger analysis |
| GET | `/api/v1/analyses/{id}` | Analysis detail |
| GET | `/api/v1/analyses/fermentation/{id}` | Analyses for a fermentation |
| GET | `/api/v1/recommendations/{id}` | Recommendation detail |
| PUT | `/api/v1/recommendations/{id}/apply` | Apply recommendation |
| GET | `/api/v1/fermentations/{id}/advisories` | List advisories |
| POST | `/api/v1/advisories/{id}/acknowledge` | Acknowledge advisory |

## Winery Module

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/admin/wineries` | Create winery |
| GET | `/api/v1/admin/wineries` | List wineries |
| GET | `/api/v1/admin/wineries/{id}` | Get winery |
| GET | `/api/v1/admin/wineries/code/{code}` | Get winery by code |
| PATCH | `/api/v1/admin/wineries/{id}` | Update winery |
| DELETE | `/api/v1/admin/wineries/{id}` | Delete winery |

## Fruit Origin Module

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