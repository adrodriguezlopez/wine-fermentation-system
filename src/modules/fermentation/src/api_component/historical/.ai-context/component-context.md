# Component Context: API Component - Historical Data (Fermentation Module)

> **Parent Context**: See `../../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`
> **Related ADR**: [ADR-032: Historical Data API Layer](../../../../../.ai-context/adr/ADR-032-historical-data-api-layer.md)

## Component responsibility
**HTTP REST API interface** for querying historical fermentation data imported via ETL pipeline, providing pattern extraction for the Analysis Engine, and managing ETL import operations.

**Position in module**: Presentation layer exposing HTTP endpoints with JWT authentication, multi-tenant authorization (winery_id scoping), request/response serialization, and read-only access to historical fermentation data with `data_source='HISTORICAL'` filter.

**Architectural Decision:** Following ADR-032 and ADR-034, this component implements FastAPI router with separate endpoints namespace (`/api/v1/historical`) for historical data operations. ADR-034 refactored service dependencies: replaced redundant HistoricalDataService with FermentationService (data_source="HISTORICAL"), SampleService, and new PatternAnalysisService for statistical aggregation. This eliminates 75% code redundancy while maintaining all endpoint functionality.

## Architecture pattern
**RESTful API Pattern** with FastAPI framework, dependency injection, and multi-tenant authorization.

**Design approach**: Clean separation between router (endpoint definitions), schemas (request/response DTOs), and business logic (HistoricalDataService), with auth dependencies injecting UserContext for automatic winery_id scoping.

- **Router**: historical_router (8 endpoints: 3 queries + 1 patterns + 1 statistics + 3 import management)
- **Request Schemas**: 
  - HistoricalFermentationQueryRequest (filters: winery_id, date range, fruit_origin, status, pagination)
  - ImportRequest (file upload with UploadFile)
  - Empty bodies for GET endpoints
- **Response Schemas**: 
  - HistoricalFermentationResponse (fermentation data with data_source='HISTORICAL')
  - PaginatedHistoricalFermentationsResponse (list with pagination metadata)
  - HistoricalSampleResponse (sample data)
  - PatternResponse (aggregated patterns for Analysis Engine: avg temps, densities, durations, success rates)
  - StatisticsResponse (dashboard metrics: total fermentations, avg duration, success rate, common issues)
  - ImportResponse (import job details: status, progress, errors)
  - ImportJobListResponse (list of import jobs)
- **Authentication**: JWT token validation via `get_current_user` dependency from shared auth module (ADR-007)
- **Authorization**: 
  - All endpoints: ADMIN can access all wineries, regular users scoped to their own winery_id
  - Multi-tenant filtering: Automatic winery_id injection from JWT token
  - Import endpoints: ADMIN or winery owner can trigger imports
- **Historical Namespace**: All endpoints under `/api/v1/historical` (separates historical from active data)
- **Error Handling**: HTTP exception handlers mapping service errors to appropriate status codes (404 not found, 400 validation, 403 forbidden)
- **Data flow**: HTTP Request → Auth Middleware → Multi-Tenant Scoping → Router → HistoricalDataService → Repository (with data_source filter) → Response Serialization
- **Extension points**: Export endpoints, advanced filtering, data quality reports
- **Integration strategy**: Depends on HistoricalDataService (service_component), reuses FermentationRepository/SampleRepository with data_source='HISTORICAL', integrates with ETL service (ADR-019) for import triggers

## Component interfaces

### **Receives from (HTTP Clients)**
**Query endpoints (3):**
- **GET /api/v1/historical/fermentations**: List historical fermentations with filters (winery, date range, fruit origin, status, pagination)
- **GET /api/v1/historical/fermentations/{id}**: Retrieve single historical fermentation by ID
- **GET /api/v1/historical/fermentations/{id}/samples**: List samples for one historical fermentation

**Pattern extraction endpoint (1):**
- **GET /api/v1/historical/patterns**: Extract aggregated patterns for Analysis Engine (query params: winery_id, fruit_origin_id, date_range)
  - Returns: AVG temperatures, densities, durations by fruit origin
  - Returns: Success rates, stuck fermentation rates
  - Returns: Common issue patterns

**Statistics endpoint (1):**
- **GET /api/v1/historical/statistics**: Dashboard metrics (total fermentations, avg duration, success rate, common issues)

**Import management endpoints (3):**
- **POST /api/v1/historical/import**: Trigger ETL import with Excel file upload (multipart/form-data)
- **GET /api/v1/historical/imports**: List import jobs with status (pending, running, completed, failed)
- **GET /api/v1/historical/imports/{id}**: Get import job details (progress, errors, fermentation count)

### **Provides to (HTTP Clients)**
- JSON responses with Pydantic serialization
- HTTP status codes: 200 (OK), 201 (Created - import triggered), 400 (Validation Error), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Server Error)
- OpenAPI documentation: Swagger UI at /docs, ReDoc at /redoc
- Multi-tenant filtered responses (automatic winery_id scoping)
- Aggregated pattern data for Analysis Engine
- Import job tracking and progress monitoring

### **Uses (Internal Dependencies)**
- **Service Component (ADR-034 Refactored)**: 
  - **FermentationService**: get_fermentations_by_winery(data_source="HISTORICAL"), get_fermentation() for fermentation queries
  - **SampleService**: get_samples_by_fermentation() with data_source filtering for sample queries
  - **PatternAnalysisService**: extract_patterns(data_source="HISTORICAL") for statistical aggregation
  - ~~HistoricalDataService~~ (DEPRECATED - removed redundancy, see ADR-034)
- **Repository Component**: 
  - FermentationRepository (via services with `data_source='HISTORICAL'` filter)
  - SampleRepository (via services with `data_source='HISTORICAL'` filter)
- **ETL Service** (service_component): ETLService for import triggers (ADR-019)
- **Auth Module** (shared/auth): `get_current_user` dependency for authentication and authorization
- **Domain Entities**: Fermentation, BaseSample for type hints and response serialization
- **Domain Errors**: FermentationNotFoundError, ValidationError

## Key patterns implemented
- **Historical Namespace**: `/api/v1/historical/*` prefix for historical data operations (separates from active data)
- **RESTful API Design**: Resource-based URLs with standard HTTP methods
- **Dependency Injection**: FastAPI dependencies for auth, services, database sessions
- **Multi-Tenant Authorization**: Automatic winery_id scoping from JWT (ADMIN can access all)
- **Data Source Filtering**: All queries filtered by `data_source='HISTORICAL'` (ADR-029)
- **Request/Response DTOs**: Separate Historical* Pydantic schemas for clarity
- **Error Handling**: Consistent JSON error responses with HTTP status codes
- **API Versioning**: `/api/v1` prefix for future backward compatibility
- **OpenAPI**: Auto-generated documentation from Pydantic schemas
- **Pagination**: Standard limit/offset pattern with total count metadata
- **Read-Only Access**: Historical data is immutable (no POST/PATCH/DELETE for fermentations)
- **Pattern Extraction**: Aggregated data specifically designed for Analysis Engine consumption
- **Import Management**: File upload with multipart/form-data, job tracking, progress monitoring

## Business rules enforced
- **Multi-tenant isolation**: All queries auto-scoped to user's winery_id (unless ADMIN)
- **Historical data immutability**: No modifications to historical fermentations/samples
- **Data source filtering**: All queries must have `data_source='HISTORICAL'` filter
- **Authorization**: Users can only query their own winery's historical data (ADMIN exception)
- **Import authorization**: Only ADMIN or winery owner can trigger imports
- **Pattern extraction**: Aggregations must respect winery_id boundaries

## Connection with other components
**Service Component (HistoricalDataService)**: Receives business logic for queries, patterns, statistics  
**Repository Component**: Uses FermentationRepository and SampleRepository with data_source filter  
**ETL Service**: Triggers import operations for file uploads  
**Auth Module**: Receives JWT authentication and UserContext for authorization  
**Analysis Engine** (future): Consumes pattern extraction endpoint for recommendations  
**Frontend** (future): Displays historical data dashboards and import management UI

## Implementation status

**Status:** 📋 **PROPOSED** (Jan 13, 2026)  
**Related ADR:** [ADR-032: Historical Data API Layer](../../../../../.ai-context/adr/ADR-032-historical-data-api-layer.md)

**Planned Components:**
- 📋 historical_router.py: FastAPI router with 8 endpoints
- 📋 schemas/requests/: HistoricalFermentationQueryRequest, ImportRequest
- 📋 schemas/responses/: HistoricalFermentationResponse, PatternResponse, ImportResponse, StatisticsResponse
- 📋 dependencies/services.py: Dependency injection for HistoricalDataService, ETLService

**Test Plan:**
- 33 API tests (endpoint validation, authorization, multi-tenancy, error handling)
- 8 integration tests (end-to-end with real database, ETL integration, pattern extraction)

**Implementation Phases:**
1. ✅ ADR-032 document created (architecture, endpoints, test plan)
2. 📋 Phase 1: Service Layer (HistoricalDataService) - 2 hours, 12 unit tests
3. 📋 Phase 2: DTOs (Request/Response schemas) - 1 hour
4. 📋 Phase 3: API Router (historical_router.py) - 3 hours, 33 API tests
5. 📋 Phase 4: Integration Tests - 2 hours, 8 integration tests
6. 📋 Phase 5: Documentation & Commit - 1 hour

**Estimated Effort:** 9 hours (1 day)

**Dependencies:**
- ✅ ADR-019: ETL Pipeline complete (import capability exists)
- ✅ ADR-030: FruitOriginService orchestration (fruit origin data available)
- ✅ ADR-031: TransactionScope pattern (transaction coordination)
- ✅ ADR-029: data_source field in entities (historical filter enabled)
- ✅ ADR-006: API layer patterns (FastAPI, Pydantic, auth integration)
- ✅ ADR-025: Multi-tenancy architecture (winery_id scoping)

**Unblocks:**
- Analysis Engine (ADR-020): Pattern extraction provides historical trends
- Frontend (ADR-023): Historical data dashboards and import management UI
- Action Tracking (ADR-022): Historical context for recommendations

## Key implementation considerations
- **Read-only API**: Historical data is immutable (no POST/PATCH/DELETE for fermentations)
- **Async operations**: All endpoint handlers async for FastAPI compatibility
- **Multi-tenant security**: All queries must respect winery_id boundaries
- **Data source filtering**: Every repository call must include `data_source='HISTORICAL'`
- **Pattern extraction**: Aggregations designed for Analysis Engine (not general analytics)
- **Import management**: File upload with validation, job tracking, progress callbacks
- **Error handling**: Specific exception types for different failure scenarios (404, 403, 400)
- **Type safety**: Strict typing with domain entities and Historical* DTOs
- **OpenAPI documentation**: All endpoints documented with request/response examples

## Future enhancements
- **Export functionality**: Download historical data as Excel/CSV
- **Advanced filtering**: Complex queries (multiple fruit origins, date ranges, custom fields)
- **Data quality reports**: Validation errors, missing data, outliers
- **Comparison tools**: Compare historical vs active fermentations
- **Bulk operations**: Batch import, batch update metadata
- **Audit trail**: Track who accessed what historical data when
- **Caching**: Redis cache for pattern extraction (expensive aggregations)
- **Migration path**: If historical data grows significantly, extract to separate module
