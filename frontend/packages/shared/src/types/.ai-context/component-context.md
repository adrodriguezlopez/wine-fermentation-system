# Component Context: Types (`packages/shared/src/types/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md` for full backend DTO shapes

## Component responsibility

**TypeScript type definitions** that mirror all backend response and request shapes. These types are the single source of truth for data shapes across both apps. Every API function, hook, and component that touches server data uses types from here.

**Rule**: Types here must match the backend exactly. When a backend DTO changes, update the type here first, then fix downstream compilation errors.

## Architecture pattern

Plain TypeScript interfaces and enums — no runtime code. Organized one file per backend domain module.

## Files

| File | Contents |
|------|---------|
| `auth.ts` | `UserRole` enum, `JwtPayload`, `LoginRequest`, `LoginResponse`, `UserContext` |
| `fermentation.ts` | `Fermentation`, `FermentationStatus` enum, `CreateFermentationDto`, `BlendSourceDto`, `UpdateFermentationDto` |
| `sample.ts` | `Sample`, `SampleType` enum, `CreateSampleDto` |
| `protocol.ts` | `Protocol`, `ProtocolStep`, `CreateProtocolDto`, `CreateStepDto` |
| `execution.ts` | `ProtocolExecution`, `ProtocolExecutionStatus` enum, `StepCompletion`, `StartExecutionDto` |
| `analysis.ts` | `Analysis`, `AnalysisStatus` enum, `TriggerAnalysisDto`, `HistoricalComparison` |
| `anomaly.ts` | `Anomaly`, `AnomalyType` enum, `SeverityLevel` enum, `DeviationScore` |
| `recommendation.ts` | `Recommendation`, `RecommendationCategory` enum, `ConfidenceLevel` enum, `ApplyRecommendationDto` |
| `advisory.ts` | `Advisory`, `AdvisoryType` enum |
| `alert.ts` | `Alert`, `AlertType` enum, `AlertStatus` enum |
| `action.ts` | `WinemakerAction`, `ActionType` enum, `ActionOutcome` enum, `CreateActionDto`, `UpdateActionOutcomeDto` |
| `winery.ts` | `Winery`, `CreateWineryDto`, `UpdateWineryDto` |
| `fruit-origin.ts` | `Vineyard`, `HarvestLot`, `CreateVineyardDto`, `CreateHarvestLotDto` |
| `pagination.ts` | `PaginatedResponse<T>`, `PaginationParams` |
| `errors.ts` | `ApiError` (wraps `{ detail: string }` from backend), `AuthExpiredError` |
| `index.ts` | Re-exports everything — consumers import from `@shared/types` |

## Key type shapes

```typescript
// Fermentation status — backend canonical values
enum FermentationStatus { ACTIVE = 'ACTIVE', SLOW = 'SLOW', STUCK = 'STUCK', COMPLETED = 'COMPLETED' }

// Paginated response wrapper — used by list endpoints
interface PaginatedResponse<T> { items: T[]; total: number; page: number; size: number; }

// API error — backend always returns { detail: string } for errors
interface ApiError { detail: string; status: number; }

// User context — extracted from JWT, available everywhere
interface UserContext { user_id: number; email: string; role: UserRole; winery_id: number; }
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 1 / packages/shared
