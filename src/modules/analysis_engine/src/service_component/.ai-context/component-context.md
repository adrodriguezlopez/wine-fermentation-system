# Component Context: Service Component — Analysis Engine

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Intelligent analysis orchestration** — coordinates the comparison → anomaly detection → recommendation pipeline for fermentation monitoring.

## Architecture pattern
**Service Layer** with dependency injection of `AsyncSession` (direct, not `ISessionManager` — analysis_engine services query across multiple entities per request).

## Services (`src/service_component/services/`)

| Service | Responsibility |
|---------|---------------|
| `AnalysisOrchestratorService` | Entry point. Manages `Analysis` lifecycle; coordinates sub-services |
| `ComparisonService` | Finds historically similar fermentations; computes `ComparisonResult` |
| `AnomalyDetectionService` | Applies 8 expert-validated detection algorithms; returns `Anomaly` list |
| `RecommendationService` | Maps anomalies → `RecommendationTemplate` → `Recommendation` list |
| `ProtocolAnalysisIntegrationService` | Confidence boost from protocol compliance; generates `ProtocolAdvisory` (ADR-037) |

## Key patterns
- **Session injection**: All services receive `AsyncSession` in `__init__` — NOT `ISessionManager`
- **Pipeline**: `Orchestrator` → `Comparison` → `AnomalyDetection` → `Recommendation`
- **Expert thresholds**: All anomaly detection thresholds validated by Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)
- **Confidence formula (ADR-020)**: `0.7×pattern_match + 0.2×sample_count_norm + 0.1×recency`
- **Protocol confidence boost (ADR-037)**: `adjusted = base × (0.5 + compliance_score / 100.0)`

## Testing approach
Unit tests use `AsyncMock` for session mocking (services use `AsyncSession` directly, not `ISessionManager`). For service-level tests where no DB is needed, pass a plain `MagicMock` session.

## Implementation status
**Status:** ✅ Complete  
**Last Updated:** April 2026  
**Tests:** ~85 unit tests (orchestrator, comparison, anomaly detection, recommendation, protocol integration)
