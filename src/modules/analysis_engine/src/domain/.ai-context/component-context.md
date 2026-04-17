# Component Context: Domain — Analysis Engine

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Defines the core business model, entities, value objects, enums, and repository interfaces for the Analysis Engine module. All analysis logic depends on abstractions defined here — the domain never depends on infrastructure.

## Architecture pattern
- **DDD**: Entities with domain behavior, immutable value objects, enum-driven state
- **Dependency Inversion**: Repository interfaces defined here, implemented in repository_component

## Entities (`src/domain/entities/`)

| Entity | Responsibility |
|--------|---------------|
| `Analysis` | Aggregate root — links fermentation to full analysis result. Status lifecycle: PENDING → IN_PROGRESS → COMPLETED/FAILED |
| `Anomaly` | A detected deviation. Holds type, severity, deviation_score (JSONB), resolution tracking |
| `Recommendation` | Actionable suggestion derived from an anomaly + template. Tracks application |
| `RecommendationTemplate` | Reusable template for a category of recommendation. Seeded at startup |
| `ProtocolAdvisory` | Advisory emitted to the Protocol Engine after analysis (ADR-037) |

**Note:** All entities inherit from `src.shared.infra.orm.base_entity.Base` (not `BaseEntity`). UUIDs as primary keys. JSONB columns for value objects.

## Value Objects (`src/domain/value_objects/`)

| Value Object | Description |
|--------------|-------------|
| `ComparisonResult` | Frozen dataclass — result of historical baseline comparison |
| `ConfidenceLevel` | Multi-dimensional confidence [0.0–1.0] with categorical label |
| `DeviationScore` | Normalized deviation magnitude — supports both z-score and threshold modes |

All value objects are `@dataclass(frozen=True)` with `to_dict()` / `from_dict()` for JSONB persistence.

## Enums (`src/domain/enums/`)

| Enum | Values |
|------|--------|
| `AnalysisStatus` | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| `AnomalyType` | 8 types (STUCK_FERMENTATION, TEMPERATURE_OUT_OF_RANGE_CRITICAL, VOLATILE_ACIDITY_HIGH, DENSITY_DROP_TOO_FAST, HYDROGEN_SULFIDE_RISK, TEMPERATURE_SUBOPTIMAL, UNUSUAL_DURATION, ATYPICAL_PATTERN) |
| `SeverityLevel` | CRITICAL, WARNING, INFO |
| `RiskLevel` | CRITICAL, HIGH, MEDIUM, LOW |
| `AdvisoryType` | ACCELERATE_STEP, SKIP_STEP, ADD_STEP |
| `RecommendationCategory` | 11 categories (TEMPERATURE_CONTROL, NUTRIENT_MANAGEMENT, AERATION_REMONTAGE, ...) |

## Repository Interfaces (`src/domain/repositories/`)

- `IAnalysisRepository` — CRUD + status queries
- `IAnomalyRepository` — by analysis, by severity
- `IRecommendationRepository` — by analysis, by category
- `IRecommendationTemplateRepository` — by anomaly type
- `IProtocolAdvisoryRepository` — by fermentation, by type

## Key design decisions
- **UUID primary keys** (not integer) — analysis_engine uses `PGUUID(as_uuid=True)`
- **JSONB for value objects** — `comparison_result`, `confidence_level`, `deviation_score` stored as JSONB
- **No cross-module ORM FK** — `fermentation_id`, `winery_id` are plain UUID columns (not FKs)
- **Python-level defaults in `__init__`** — so entities work in unit tests without a real DB

## Implementation status
**Status:** ✅ Complete  
**Last Updated:** April 2026
