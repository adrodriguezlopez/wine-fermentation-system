# ADR-032: Historical Data API Layer

**Status:** 📋 **Proposed**  
**Date Created:** January 13, 2026  
**Deciders:** AI Assistant + Álvaro (Product Owner)  
**Related ADRs:**
- ADR-019: ETL Pipeline for Historical Data (provides ETL service) ✅
- ADR-030: ETL Cross-Module Architecture (FruitOriginService orchestration) ✅
- ADR-031: Cross-Module Transaction Coordination (TransactionScope pattern) ✅
- ADR-029: Data Source Field for Historical Tracking (data_source field) ✅
- ADR-006: API Layer Design (FastAPI patterns)
- ADR-025: Multi-Tenancy Security (winery_id scoping)

---

## Context

The ETL pipeline (ADR-019, 030, 031) successfully imports historical fermentation data from Excel files. However, **no API exists** to query, search, or analyze this imported data.

**Current State:**
- ✅ ETLService can import historical data (21 unit tests + 12 integration tests)
- ✅ FermentationRepository has `list_by_data_source()` method (ADR-029)
- ✅ SampleRepository has `list_by_data_source()` method (ADR-029)
- ✅ Data properly tagged with `data_source='HISTORICAL'`
- ❌ No REST endpoints to access historical fermentations
- ❌ No way to extract patterns for analysis engine
- ❌ No import management API (trigger, monitor, list imports)

**Business Need:**
- Winemakers need to **search/view** imported historical fermentations
- Analysis Engine needs **pattern extraction** from historical data for anomaly detection
- System needs **import management** UI (upload Excel, monitor progress, view results)
- Multi-tenant security: Each winery only sees their historical data

**Problem Statement:**
The ETL pipeline is complete but **data is trapped** - no API to access it. This blocks:
1. Frontend development (can't display historical data)
2. Analysis Engine development (can't fetch reference patterns)
3. Import workflow UI (can't trigger/monitor imports)

---

## Decision

Create **Historical Data API Layer** within the **Fermentation module** with:

### 1. **Module Location** 
**Keep in Fermentation module** (`src/modules/fermentation/`) - Historical fermentations ARE fermentations (same entities).
- Design allows future extraction to separate `historical-data` module if it grows
- ETL service already in Fermentation module
- Reuses existing domain entities (Fermentation, Sample) with `data_source` filter

### 2. **Service Layer**
Create **new HistoricalDataService** (`src/modules/fermentation/src/service_component/historical/`)
- **Responsibility**: Query, aggregate, and analyze historical fermentation data
- **Methods**:
  - `list_historical_fermentations()`: Paginated list with filters
  - `get_historical_fermentation()`: Single fermentation by ID
  - `get_patterns()`: Aggregate patterns for analysis (avg glucose decay, ethanol rise)
  - `get_statistics()`: Aggregate stats (count, success rate, avg duration)
- **Reuses**: FermentationRepository, SampleRepository (with `data_source='HISTORICAL'`)

### 3. **API Component Structure**
Create **new api_component subfolder** (`src/modules/fermentation/src/api_component/historical/`)
- Follows existing pattern (fruit_origin has `api_component/`, winery has `api_component/`)
- Separate component-context.md for documentation
- Router mounted at `/api/v1/historical/...`

### 4. **DTOs (Request/Response)**
Create **separate Historical DTOs** for clarity and extensibility:
- **HistoricalFermentationResponse**: Includes `import_id`, `imported_at`, `source_file`
- **HistoricalSampleResponse**: Historical-specific sample representation
- **PatternResponse**: Aggregated pattern data for analysis
- **StatisticsResponse**: Aggregate metrics
- **ImportRequest**: Trigger import with Excel file
- **ImportResponse**: Import job details with progress

### 5. **Import Management API**
Expose ETL functionality via REST API:
- `POST /api/v1/historical/import` - Upload Excel and trigger ETL
- `GET /api/v1/historical/imports` - List import jobs
- `GET /api/v1/historical/imports/{id}` - Get import details with results

---

## API Endpoints Design

### Historical Fermentations (Read-Only)
```
GET  /api/v1/historical/fermentations
     ?winery_id={id}           # Auto-scoped by auth
     &variety={variety}        # Filter by grape variety
     &year={year}              # Filter by harvest year
     &success={true|false}     # Filter by outcome
     &limit=50&offset=0        # Pagination

GET  /api/v1/historical/fermentations/{id}
     # Get single historical fermentation with samples

GET  /api/v1/historical/fermentations/{id}/samples
     # Get samples for historical fermentation
```

### Pattern Extraction (For Analysis Engine)
```
GET  /api/v1/historical/patterns
     ?variety={variety}        # Required: grape variety
     &year={year}              # Optional: specific year
     &winery_id={id}           # Auto-scoped by auth
     
     Response: {
       "variety": "Chardonnay",
       "sample_count": 150,
       "avg_glucose_decay_rate": 0.8,  # g/L per day
       "avg_ethanol_rise_rate": 0.5,   # % per day
       "avg_duration_days": 18.5,
       "percentiles": {
         "glucose_p10": 0.6,
         "glucose_p50": 0.8,
         "glucose_p90": 1.1
       }
     }
```

### Statistics (Dashboard/Reporting)
```
GET  /api/v1/historical/statistics
     ?winery_id={id}           # Auto-scoped by auth
     
     Response: {
       "total_fermentations": 450,
       "total_samples": 12500,
       "varieties": ["Chardonnay", "Merlot", ...],
       "years": [2020, 2021, 2022, 2023],
       "success_rate": 0.92,
       "avg_duration_days": 19.3
     }
```

### Import Management
```
POST /api/v1/historical/import
     Content-Type: multipart/form-data
     Body: { file: <excel_file> }
     
     Response: {
       "import_id": "uuid-123",
       "status": "processing",
       "started_at": "2026-01-13T10:00:00Z"
     }

GET  /api/v1/historical/imports
     # List all imports for winery (paginated)

GET  /api/v1/historical/imports/{id}
     # Get import details
     Response: {
       "import_id": "uuid-123",
       "status": "completed",
       "started_at": "2026-01-13T10:00:00Z",
       "completed_at": "2026-01-13T10:05:23Z",
       "total_rows": 450,
       "successful_imports": 425,
       "failed_imports": 25,
       "results": {
         "fermentations_created": 85,
         "samples_created": 425,
         "errors": [...]
       }
     }
```

---

## Architecture

### Component Structure
```
src/modules/fermentation/
├── src/
│   ├── api_component/           # NEW
│   │   ├── historical/          # NEW: Historical Data API
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   └── historical_router.py    # NEW: 8 endpoints
│   │   │   ├── schemas/
│   │   │   │   ├── requests/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── historical_requests.py   # Filters, pagination
│   │   │   │   │   └── import_requests.py       # Import file upload
│   │   │   │   └── responses/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── historical_responses.py  # Historical DTOs
│   │   │   │       ├── pattern_responses.py     # Pattern data
│   │   │   │       └── import_responses.py      # Import results
│   │   │   ├── dependencies/
│   │   │   │   ├── __init__.py
│   │   │   │   └── services.py  # Dependency injection
│   │   │   └── .ai-context/
│   │   │       └── component-context.md  # NEW
│   │   └── __init__.py
│   │
│   ├── service_component/
│   │   ├── etl/                 # EXISTING (ADR-019)
│   │   │   ├── etl_service.py
│   │   │   └── ...
│   │   └── historical/          # NEW: Historical Data Service
│   │       ├── __init__.py
│   │       └── historical_data_service.py  # NEW
│   │
│   └── domain/                  # EXISTING (reuse)
│       ├── entities/
│       │   ├── fermentation.py  # Has data_source field
│       │   └── samples.py       # Has data_source field
│       └── repositories/
│           ├── fermentation_repository_interface.py
│           └── sample_repository_interface.py

tests/
└── api/
    └── historical/              # NEW
        ├── __init__.py
        ├── test_historical_fermentations_api.py  # ~15 tests
        ├── test_patterns_api.py                  # ~8 tests
        └── test_import_management_api.py         # ~10 tests
        # Total: ~33 API tests
```

---

## Implementation Plan (TDD)

### Phase 1: Historical Data Service (GREEN - 2 hours)
**Goal:** Create service layer for querying historical data

**Service Methods:**
```python
class HistoricalDataService:
    async def list_historical_fermentations(
        self,
        winery_id: int,
        variety: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Fermentation]:
        """List historical fermentations with filters."""
        
    async def get_historical_fermentation(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> Optional[Fermentation]:
        """Get single historical fermentation."""
        
    async def get_patterns(
        self,
        winery_id: int,
        variety: str
    ) -> PatternData:
        """Get aggregated patterns for analysis engine."""
        
    async def get_statistics(
        self,
        winery_id: int
    ) -> StatisticsData:
        """Get aggregate statistics."""
```

**Unit Tests:** 12 tests
- test_list_historical_fermentations_success
- test_list_historical_fermentations_with_variety_filter
- test_list_historical_fermentations_with_year_filter
- test_list_historical_fermentations_pagination
- test_list_historical_fermentations_empty
- test_get_historical_fermentation_success
- test_get_historical_fermentation_not_found
- test_get_historical_fermentation_wrong_winery (multi-tenant)
- test_get_patterns_success
- test_get_patterns_no_data
- test_get_statistics_success
- test_get_statistics_empty_winery

**Implementation Steps:**
1. Create `src/modules/fermentation/src/service_component/historical/historical_data_service.py`
2. Implement methods using FermentationRepository.list_by_data_source()
3. Add pattern aggregation logic (calculate avg rates, percentiles)
4. Add statistics aggregation logic
5. Run tests: `poetry run pytest tests/unit/service/historical/ -v`

---

### Phase 2: API DTOs (GREEN - 1 hour)
**Goal:** Create request/response models for API

**Response DTOs:**
```python
# historical_responses.py
class HistoricalFermentationResponse(BaseModel):
    id: int
    code: str
    variety: str
    harvest_date: date
    start_date: date
    end_date: Optional[date]
    status: str
    data_source: str = "HISTORICAL"
    imported_at: Optional[datetime]
    sample_count: int

class HistoricalSampleResponse(BaseModel):
    id: int
    fermentation_id: int
    sample_date: datetime
    glucose_gl: float
    ethanol_pct: float
    temperature_c: float
    data_source: str = "HISTORICAL"

# pattern_responses.py
class PatternResponse(BaseModel):
    variety: str
    sample_count: int
    avg_glucose_decay_rate: float
    avg_ethanol_rise_rate: float
    avg_duration_days: float
    percentiles: Dict[str, float]

# import_responses.py
class ImportResponse(BaseModel):
    import_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_rows: int
    successful_imports: int
    failed_imports: int
```

**No tests needed** (Pydantic models validate themselves)

---

### Phase 3: API Router (RED → GREEN - 3 hours)
**Goal:** Implement REST endpoints with authorization

**Endpoints to implement:**
1. `GET /api/v1/historical/fermentations` - List with filters
2. `GET /api/v1/historical/fermentations/{id}` - Get one
3. `GET /api/v1/historical/fermentations/{id}/samples` - Get samples
4. `GET /api/v1/historical/patterns` - Pattern extraction
5. `GET /api/v1/historical/statistics` - Statistics
6. `POST /api/v1/historical/import` - Trigger import
7. `GET /api/v1/historical/imports` - List imports
8. `GET /api/v1/historical/imports/{id}` - Get import details

**API Tests:** 33 tests
- **List Fermentations (10 tests)**:
  - test_list_historical_fermentations_success
  - test_list_historical_fermentations_with_variety_filter
  - test_list_historical_fermentations_with_year_filter
  - test_list_historical_fermentations_pagination
  - test_list_historical_fermentations_empty
  - test_list_historical_fermentations_multi_tenant_isolation
  - test_list_historical_fermentations_unauthorized
  - test_list_historical_fermentations_invalid_params
  - test_list_historical_fermentations_excludes_current_data
  - test_list_historical_fermentations_ordering
  
- **Get Single Fermentation (5 tests)**:
  - test_get_historical_fermentation_success
  - test_get_historical_fermentation_not_found
  - test_get_historical_fermentation_wrong_winery
  - test_get_historical_fermentation_unauthorized
  - test_get_historical_fermentation_with_samples
  
- **Pattern Extraction (8 tests)**:
  - test_get_patterns_success
  - test_get_patterns_with_variety_filter
  - test_get_patterns_no_data_returns_empty
  - test_get_patterns_multi_tenant_scoped
  - test_get_patterns_unauthorized
  - test_get_patterns_missing_variety_param
  - test_get_patterns_calculates_averages_correctly
  - test_get_patterns_calculates_percentiles_correctly
  
- **Statistics (3 tests)**:
  - test_get_statistics_success
  - test_get_statistics_empty_winery
  - test_get_statistics_unauthorized
  
- **Import Management (7 tests)**:
  - test_trigger_import_success
  - test_trigger_import_invalid_file
  - test_trigger_import_unauthorized
  - test_list_imports_success
  - test_list_imports_pagination
  - test_get_import_details_success
  - test_get_import_details_not_found

**Implementation Steps:**
1. Write RED tests first: `tests/api/historical/test_*.py`
2. Create `historical_router.py` with 8 endpoints
3. Implement authorization (ADMIN or own winery)
4. Wire up HistoricalDataService
5. Add error handling (404, 403, 400)
6. Run tests: `poetry run pytest tests/api/historical/ -v`

---

### Phase 4: Integration Tests (GREEN - 2 hours)
**Goal:** Test with real database

**Integration Tests:** 8 tests
- test_list_historical_fermentations_with_real_data
- test_get_patterns_aggregates_real_samples
- test_statistics_calculates_from_real_data
- test_import_excel_creates_historical_data
- test_multi_tenant_isolation_with_real_db
- test_pagination_with_large_dataset
- test_pattern_percentiles_with_real_distribution
- test_import_idempotency_with_real_db

**Implementation Steps:**
1. Create `tests/integration/historical/test_historical_integration.py`
2. Use real PostgreSQL test database
3. Seed test data (historical fermentations)
4. Run full API flow
5. Verify multi-tenancy isolation
6. Run tests: `poetry run pytest tests/integration/historical/ -v`

---

### Phase 5: Documentation & Context Updates (1 hour)
**Goal:** Update all documentation

**Updates Required:**
1. Create `api_component/historical/.ai-context/component-context.md`
2. Update `src/modules/fermentation/.ai-context/module-context.md`:
   - Add Historical Data Service (12 unit tests)
   - Add Historical Data API (33 API tests + 8 integration)
   - Update total test count
3. Update ADR-INDEX.md:
   - Mark ADR-032 as IMPLEMENTED
   - Add to summary table
   - Add Quick Reference
4. Update service_component component-context (if exists)

---

## Authorization & Security

**Multi-Tenancy:**
- All queries auto-scoped by `winery_id` from JWT token
- Historical data filtered by `data_source='HISTORICAL'` AND `winery_id`

**Role Requirements:**
- **ADMIN**: Full access to all winery historical data
- **WINEMAKER**: Access to own winery historical data only

**Endpoint Security:**
```python
# List fermentations
@router.get("/fermentations")
async def list_historical_fermentations(
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[HistoricalDataService, Depends(get_historical_service)],
    variety: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    # Auto-scope by user.winery_id (ADR-025)
    return await service.list_historical_fermentations(
        winery_id=user.winery_id,
        variety=variety,
        year=year,
        limit=limit,
        offset=offset
    )
```

---

## Consequences

### ✅ Benefits
1. **Unblocks Analysis Engine**: Can now fetch historical patterns for anomaly detection
2. **Completes ETL Story**: ETL pipeline now has API to query imported data
3. **Frontend Ready**: UI can display/search historical fermentations
4. **Import Management**: Users can trigger/monitor imports via UI
5. **Reuses Infrastructure**: Leverages existing repositories, no new entities
6. **Clean Architecture**: Separate service layer, testable, maintainable
7. **Multi-Tenant Secure**: Winery-scoped queries, no data leakage

### ⚠️ Risks & Mitigations
1. **Performance - Large Datasets**:
   - Risk: Querying 100K+ samples for patterns could be slow
   - Mitigation: Add database indexes on (data_source, winery_id, variety), use LIMIT
   
2. **Module Size**:
   - Risk: Fermentation module grows larger
   - Mitigation: Design allows extraction to separate module later

3. **Pattern Calculation Complexity**:
   - Risk: Statistical calculations might be complex
   - Mitigation: Start simple (averages, percentiles), iterate based on analysis engine needs

### 🔮 Future Enhancements
- **Caching**: Cache pattern/statistics responses (Redis)
- **Advanced Filters**: Filter by success rate, duration range, quality metrics
- **Export API**: Export historical data to Excel
- **Separate Module**: Extract to `historical-data` module if grows beyond 2K lines
- **Real-time Import Progress**: WebSocket for import progress updates

---

## Acceptance Criteria

1. ✅ HistoricalDataService created with 4 methods (12 unit tests passing)
2. ✅ API Router with 8 endpoints (33 API tests passing)
3. ✅ Integration tests with real database (8 tests passing)
4. ✅ Multi-tenant security enforced (winery_id scoping)
5. ✅ Pattern extraction works (averages, percentiles calculated)
6. ✅ Import management API functional (trigger, monitor, list)
7. ✅ Documentation complete (component-context, module-context, ADR-INDEX)
8. ✅ All tests passing: **53 new tests (12 unit + 33 API + 8 integration)**

---

## Test Summary

**Total New Tests: 53**
- Unit Tests: 12 (HistoricalDataService)
- API Tests: 33 (8 endpoints coverage)
- Integration Tests: 8 (real database)

**Estimated Implementation Time:** 9 hours (1 day)
- Phase 1: Service Layer (2h)
- Phase 2: DTOs (1h)
- Phase 3: API Router (3h)
- Phase 4: Integration Tests (2h)
- Phase 5: Documentation (1h)

---

## References

- **ETL Pipeline**: [ADR-019](./ADR-019-etl-pipeline-historical-data.md)
- **Cross-Module Orchestration**: [ADR-030](./ADR-030-etl-cross-module-architecture-refactoring.md)
- **Transaction Coordination**: [ADR-031](./ADR-031-cross-module-transaction-coordination.md)
- **Data Source Tracking**: [ADR-029](./ADR-029-data-source-field-historical-tracking.md)
- **API Layer Design**: [ADR-006](./ADR-006-api-layer-design.md)
- **Multi-Tenancy**: [ADR-025](./ADR-025-multi-tenancy-security.md)

---

## Implementation Checklist

### Phase 1: Service Layer (2h)
- [ ] Create `historical/historical_data_service.py`
- [ ] Implement `list_historical_fermentations()`
- [ ] Implement `get_historical_fermentation()`
- [ ] Implement `get_patterns()` with aggregation
- [ ] Implement `get_statistics()`
- [ ] Write 12 unit tests
- [ ] Run tests: All 12 passing ✅

### Phase 2: DTOs (1h)
- [ ] Create `schemas/responses/historical_responses.py`
- [ ] Create `schemas/responses/pattern_responses.py`
- [ ] Create `schemas/responses/import_responses.py`
- [ ] Create `schemas/requests/historical_requests.py`
- [ ] Create `schemas/requests/import_requests.py`

### Phase 3: API Router (3h)
- [ ] Create `routers/historical_router.py`
- [ ] Implement 8 endpoints
- [ ] Add authorization (ADMIN or own winery)
- [ ] Wire up dependencies
- [ ] Write 33 API tests (RED)
- [ ] Implement endpoints (GREEN)
- [ ] Run tests: All 33 passing ✅

### Phase 4: Integration Tests (2h)
- [ ] Create `tests/integration/historical/test_historical_integration.py`
- [ ] Write 8 integration tests
- [ ] Seed test data
- [ ] Verify multi-tenancy
- [ ] Run tests: All 8 passing ✅

### Phase 5: Documentation (1h)
- [ ] Create `api_component/historical/.ai-context/component-context.md`
- [ ] Update `module-context.md` (test counts, new components)
- [ ] Update ADR-INDEX.md (mark IMPLEMENTED, add Quick Reference)
- [ ] Update ADR-032 status to IMPLEMENTED
- [ ] Commit and push changes

---

**Ready to implement!** 🚀
