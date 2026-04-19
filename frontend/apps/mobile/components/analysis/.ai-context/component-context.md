# Component Context: Mobile Analysis (`apps/mobile/components/analysis/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/fermentation/[id]/analysis.tsx`

## Component responsibility

**Analysis output display** — shows the most recent analysis for a fermentation. Winemakers can see anomalies detected, recommendations, and protocol advisories. They can also trigger a new analysis run.

## Components

### `AnalysisSummaryCard.tsx`
Top-level summary card: analysis timestamp, anomaly count with highest severity, recommendation count, deviation score in DM Mono. If no analysis yet: "No analysis run yet" message.

### `RunAnalysisButton.tsx`
Button to trigger `analysisApi.triggerAnalysis(fermentationId)`. Shows spinner while running. On success: invalidates `['analysis', fermentationId]` query. On error: shows `<ErrorMessage>`.

### `RecommendationCard.tsx`
Mobile version of the recommendation card. Category label, description, `<ConfidencePill>`. "Apply" button → calls `recommendationApi.applyRecommendation`. If offline: adds to `SyncQueue` as recommendation application (online-only operation — shown as disabled with tooltip "Connect to apply").

### `AdvisoryCard.tsx`
Protocol advisory card. Advisory content text, `formatRelative(created_at)`. "Acknowledge" button → `POST /advisories/{id}/acknowledge`. After acknowledged: shows acknowledged timestamp, button hidden.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
