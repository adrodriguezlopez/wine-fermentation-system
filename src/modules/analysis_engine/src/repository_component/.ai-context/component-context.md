# Component Context: Repository Component — Analysis Engine

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence** for analysis results, anomalies, recommendations, and protocol advisories using SQLAlchemy async ORM with PostgreSQL JSONB.

## Architecture pattern
**Repository Pattern** — concrete implementations of domain interfaces. Services depend on domain interfaces; this component provides the SQLAlchemy implementations.

## Repositories (`src/repository_component/repositories/`)

| Repository | Interface | Responsibility |
|------------|-----------|---------------|
| `AnalysisRepository` | `IAnalysisRepository` | CRUD + status queries for Analysis aggregate |
| `AnomalyRepository` | `IAnomalyRepository` | Anomaly persistence with JSONB `deviation_score` |
| `RecommendationRepository` | `IRecommendationRepository` | Recommendations with template JOIN |
| `RecommendationTemplateRepository` | `IRecommendationTemplateRepository` | Template lookup by anomaly type |
| `ProtocolAdvisoryRepository` | `IProtocolAdvisoryRepository` | Advisory storage with multi-tenant scoping |

## Key design decisions
- **Direct `AsyncSession`** injection (not `ISessionManager`) — consistent with service layer
- **JSONB fields**: `deviation_score`, `comparison_result`, `confidence_level` — handled as dicts
- **UUID primary keys** throughout — `PGUUID(as_uuid=True)`
- **No cross-module FK**: `fermentation_id`, `winery_id` are plain UUID columns

## Implementation status
**Status:** ✅ Complete  
**Last Updated:** April 2026  
**Tests:** ~24 unit tests (analysis + protocol_advisory repos)
