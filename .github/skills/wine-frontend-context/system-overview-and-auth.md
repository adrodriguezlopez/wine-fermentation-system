# System Overview And Auth

## Backend Shape Relevant To Frontend

The frontend integrates with four backend modules:

- fermentation
- analysis engine
- winery
- fruit origin

At a product level, the UI serves two main audiences:

- winemakers
- admins

The system is multi-tenant by winery.

## Core Assumptions For Frontend Work

- API style is REST + JSON
- most endpoints live under `/api/v1`
- auth uses access + refresh tokens
- winery scoping is usually derived from auth context
- live-ish UX is polling-based, not WebSocket-based

## Authentication Flow

### Login

```text
POST /api/v1/auth/login
Body: { "username": "...", "password": "..." }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Refresh

```text
POST /api/v1/auth/refresh
Body: { "refresh_token": "..." }
Response: { "access_token": "...", "token_type": "bearer" }
```

### Current User

```text
GET /api/v1/auth/me
Header: Authorization: Bearer <token>
Response: { "id": 1, "email": "...", "role": "WINEMAKER|ADMIN", "winery_id": 1 }
```

Most authenticated requests use the bearer token flow above.

## User Roles

- `WINEMAKER` — operates fermentations, samples, protocols, alerts, and actions within their winery
- `ADMIN` — can also manage wineries and admin-only operations

Role-aware UI is required. Do not expose admin actions as regular winemaker actions.

## Multi-Tenancy Expectations

For most normal write operations, the frontend should not manually provide `winery_id`.

Expected default assumption:

- the backend reads winery scope from auth context
- list/detail results are already tenant-scoped

## Important Exception

Historical fermentation endpoints use a different auth/scoping pattern and require special handling.
See `endpoint-reference.md` and `domain-and-ux-constraints.md` before designing those flows.