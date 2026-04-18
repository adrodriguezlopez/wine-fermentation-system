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
| `ThresholdConfigService` | Loads anomaly detection thresholds from `config/thresholds.toml`; resolves by varietal group |

## ThresholdConfigService

| | |
|---|---|
| **File** | `src/service_component/services/threshold_config_service.py` |
| **Config (prod)** | `config/thresholds.toml` |
| **Config (tests)** | `config/thresholds_test.toml` |
| **Singleton** | Instantiated once in `src/api/dependencies.py` as `_threshold_config`; injected into `AnalysisOrchestratorService` → `AnomalyDetectionService` |

**Varietal groups:**
- `red`: Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel
- `white`: all other varietals (fallback — intentional, safe)

**`VarietalThresholds` fields** (frozen dataclass — immutable, no abbreviations):
- `temperature_critical_min_celsius`, `temperature_critical_max_celsius`
- `temperature_optimal_min_celsius`, `temperature_optimal_max_celsius`
- `volatile_acidity_warning_in_grams_per_liter`, `volatile_acidity_critical_in_grams_per_liter`
- `density_drop_max_percent_per_24_hours`
- `hydrogen_sulfide_risk_max_temperature_celsius`, `hydrogen_sulfide_risk_critical_window_days`
- `stuck_fermentation_min_density_change_points`, `stuck_fermentation_min_stall_duration_days`

**Migration path to per-winery DB overrides (Option B — when first client onboarded):**
1. Add table `winery_varietal_thresholds(id, winery_id UUID, varietal_group VARCHAR, key VARCHAR, value FLOAT)`
2. Change signature: `get_thresholds(variety)` → `get_thresholds(variety, winery_id=None)`
3. Query DB for winery row, fallback to TOML on miss
4. `AnomalyDetectionService` does **NOT** change — interface is identical
5. Seed DB from `thresholds.toml` values on first winery setup

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
**Tests:** ~212 unit tests (orchestrator, comparison, anomaly detection, recommendation, protocol integration, threshold config)
