# Component Context: API Component — Analysis Engine

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**HTTP REST API** for triggering analysis, retrieving results, and managing protocol advisories. Runs as an independent FastAPI service on port **8003**.

## Architecture pattern
**FastAPI routers** with Pydantic V2 schemas and centralized error handling via `@handle_analysis_errors` decorator.

## Routers (`src/api/routers/`)

| Router | Endpoints | Responsibility |
|--------|-----------|---------------|
| `analysis_router.py` | POST /analyses, GET /analyses/{id}, GET /analyses | Analysis lifecycle |
| `recommendation_router.py` | GET /analyses/{id}/recommendations, GET /templates | Recommendation retrieval |
| `advisory_router.py` | POST /advisories, GET /advisories/{fermentation_id} | Protocol advisory management |

## Schemas (`src/api/schemas/`)
- `requests/analysis_requests.py` — `TriggerAnalysisRequest`, `AnalysisFilter`
- `responses/analysis_responses.py` — `AnalysisResponse`, `AnomalyResponse`, `RecommendationResponse`, `ProtocolAdvisoryResponse`

## Key patterns
- **Port 8003**: Independent service (not embedded in fermentation module)
- **`@handle_analysis_errors`**: Decorator in `error_handlers.py` maps domain exceptions → HTTP codes
- **Dependency injection**: `dependencies.py` wires repositories + services using FastAPI `Depends`
- **Multi-tenancy**: `winery_id` extracted from JWT context, injected into all service calls

## Implementation status
**Status:** ✅ Complete  
**Last Updated:** April 2026
