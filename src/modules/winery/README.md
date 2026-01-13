# Winery Module API

FastAPI application for managing winery organizations (multi-tenancy root entity).

## Quick Start

### Run Development Server

```bash
# From the winery module directory
cd src/modules/winery

# Install dependencies
poetry install

# Run the API server (requires src.shared to be accessible)
# Option 1: Using uvicorn with correct Python path
PYTHONPATH=../../.. poetry run uvicorn src.main:app --reload --port 8001

# Option 2: Using docker-compose (recommended)
# See docker-compose.yml in project root
docker-compose up winery

# Option 3: Run tests (which work with current setup)
poetry run pytest tests/api/ -v
```

**Note**: The winery module is designed to run as part of the overall system. For standalone development, ensure `src.shared` is accessible in the Python path.

The API will be available at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

### Run Tests

```bash
# Run all tests (104 tests)
poetry run pytest -v

# Run only API tests (25 tests)
poetry run pytest tests/api/ -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

## API Endpoints

### Admin Namespace: `/api/v1/admin/wineries`

All endpoints require JWT authentication. Authorization varies by endpoint.

| Method | Endpoint | Authorization | Description |
|--------|----------|---------------|-------------|
| POST | `/admin/wineries` | ADMIN only | Create new winery |
| GET | `/admin/wineries` | ADMIN only | List all wineries (paginated) |
| GET | `/admin/wineries/{id}` | ADMIN or own winery | Get winery by ID |
| GET | `/admin/wineries/code/{code}` | ADMIN or own winery | Get winery by code |
| PATCH | `/admin/wineries/{id}` | ADMIN or own winery | Update winery |
| DELETE | `/admin/wineries/{id}` | ADMIN only | Soft delete winery |

### Examples

**Create Winery (ADMIN only):**
```bash
curl -X POST "http://localhost:8001/api/v1/admin/wineries" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BODEGA-001",
    "name": "My Winery",
    "location": "Napa Valley",
    "notes": "Founded 2020"
  }'
```

**Get Winery:**
```bash
curl -X GET "http://localhost:8001/api/v1/admin/wineries/1" \
  -H "Authorization: Bearer <token>"
```

**List Wineries (ADMIN only):**
```bash
curl -X GET "http://localhost:8001/api/v1/admin/wineries?limit=10&offset=0" \
  -H "Authorization: Bearer <admin_token>"
```

**Update Winery:**
```bash
curl -X PATCH "http://localhost:8001/api/v1/admin/wineries/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Winery Name",
    "location": "Sonoma"
  }'
```

**Delete Winery (ADMIN only):**
```bash
curl -X DELETE "http://localhost:8001/api/v1/admin/wineries/1" \
  -H "Authorization: Bearer <admin_token>"
```

## Architecture

### Components

- **Domain Layer**: Winery entity (`src/domain/entities/winery.py`)
- **Repository Layer**: Data access (22 unit + 18 integration tests)
- **Service Layer**: Business logic (22 unit + 17 integration tests)
- **API Layer**: REST endpoints (25 API tests) ✅ **ADR-017**

### Request/Response DTOs

**Request DTOs** (`src/api_component/schemas/requests/`):
- `WineryCreateRequest`: code, name, location (optional), notes (optional)
- `WineryUpdateRequest`: name, location, notes (code is immutable)

**Response DTOs** (`src/api_component/schemas/responses/`):
- `WineryResponse`: Full winery data with timestamps
- `PaginatedWineriesResponse`: List with pagination metadata

### Authorization Matrix

| Operation | ADMIN | User (Own Winery) | User (Other Winery) |
|-----------|-------|-------------------|---------------------|
| CREATE | ✅ | ❌ | ❌ |
| LIST | ✅ | ❌ | ❌ |
| GET by ID | ✅ | ✅ | ❌ |
| GET by code | ✅ | ✅ | ❌ |
| UPDATE | ✅ | ✅ | ❌ |
| DELETE | ✅ | ❌ | ❌ |

### Business Rules

1. **Unique code**: Winery code must be globally unique
2. **Code format**: Uppercase alphanumeric with hyphens (e.g., `BODEGA-001`)
3. **Code immutability**: Code cannot be changed after creation
4. **Deletion protection**: Cannot delete winery with active vineyards or fermentations
5. **Soft delete**: Wineries are marked as deleted, not physically removed

## Test Coverage

- **Total**: 104 tests passing (100%)
- **Unit Tests**: 44 tests (22 repository + 22 service)
- **Integration Tests**: 35 tests (18 repository + 17 service)
- **API Tests**: 25 tests
  - CREATE: 6 tests
  - GET: 8 tests (4 by ID + 4 by code)
  - LIST: 3 tests
  - UPDATE: 5 tests
  - DELETE: 3 tests

## Dependencies

- **FastAPI**: Web framework
- **Pydantic v2**: Request/response validation
- **SQLAlchemy**: ORM (async)
- **Shared Modules**:
  - `src.shared.auth`: JWT authentication + RBAC
  - `src.shared.domain.errors`: Domain error classes
  - `src.shared.wine_fermentator_logging`: Structured logging (ADR-027)

## Related ADRs

- **ADR-016**: Winery Service Layer ✅
- **ADR-017**: Winery API Design ✅
- **ADR-007**: Authentication Module (JWT + RBAC)
- **ADR-025**: Multi-Tenancy Security
- **ADR-026**: Error Handling Strategy
- **ADR-027**: Structured Logging & Observability

## Future Enhancements

- [ ] Relationship endpoints (GET vineyards, GET fermentations)
- [ ] Seed script for initial data bootstrap
- [ ] Bulk operations (import multiple wineries)
- [ ] Advanced filtering and search
- [ ] Winery statistics and analytics
- [ ] Audit trail for winery changes
