# Wine Fermentation System — Frontend Screens & API Endpoint Mapping

## 1. Dashboard / Overview Screen
**API Endpoints:**
- `GET /api/batches/active`
- `GET /api/alerts`
- `GET /api/sensors/latest`

## 2. Batch List Screen
**API Endpoints:**
- `GET /api/batches?status=&page=&limit=&sort=`

## 3. Batch Detail Screen
**API Endpoints:**
- `GET /api/batches/:id`
- `GET /api/batches/:id/readings`
- `GET /api/batches/:id/notes`
- `POST /api/batches/:id/notes`

## 4. New Batch / Create Batch Screen
**API Endpoints:**
- `POST /api/batches`
- `GET /api/recipes`
- `GET /api/tanks`

## 5. Tank / Vessel Management Screen
**API Endpoints:**
- `GET /api/tanks`
- `POST /api/tanks`
- `PUT /api/tanks/:id`
- `DELETE /api/tanks/:id`

## 6. Sensor Readings / Monitoring Screen
**API Endpoints:**
- `GET /api/sensors/:id/readings?from=&to=`
- `GET /api/sensors/:id/latest`
- WebSocket `ws://api/sensors/stream`

## 7. Alerts & Notifications Screen
**API Endpoints:**
- `GET /api/alerts?acknowledged=false`
- `PUT /api/alerts/:id/acknowledge`
- `GET /api/alert-rules`

## 8. Recipe / Parameter Template Screen
**API Endpoints:**
- `GET /api/recipes`
- `POST /api/recipes`
- `PUT /api/recipes/:id`

## 9. User Management / Settings Screen
**API Endpoints:**
- `GET /api/users/me`
- `PUT /api/users/me`
- `GET /api/settings`

## 10. Login / Authentication
**API Endpoints:**
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
