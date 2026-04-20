# Component Context: Analysis Components (`apps/web/src/components/analysis/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: Analysis engine endpoints in `.github/skills/wine-frontend-context/SKILL.md`

## Component responsibility

**Analysis, anomaly, recommendation, and advisory UI components** for the web admin app. These components visualise the output of the Analysis Engine: detected anomalies, actionable recommendations with confidence levels, and protocol advisories that suggest adjustments to the fermentation protocol.

## Components

### Analysis list
- **`AnalysisListTable.tsx`** — Table of all analyses for a fermentation. Columns: timestamp, anomaly count, top severity, deviation score badge, recommendation count. Row links to analysis report. "Run New Analysis" button at top triggers `analysisApi.triggerAnalysis` and navigates to new analysis result.

### Analysis report
- **`AnalysisReport.tsx`** — Full analysis result page. Composed of: `<AnomalyList>`, `<RecommendationList>`, `<HistoricalComparisonCard>`. Header shows analysis timestamp, fermentation ID, and a "Run Again" button.
- **`AnomalyList.tsx`** — Ordered list (highest severity first) of `<AnomalyCard>` items.
- **`AnomalyCard.tsx`** — Anomaly type label, description, severity badge (CRITICAL/HIGH/MEDIUM/LOW using `CONFIDENCE_COLOR` palette), deviation score in DM Mono (`formatDeviationScore()`), affected metric.
- **`HistoricalComparisonCard.tsx`** — Shows mean, standard deviation, and current value vs historical baseline. Deviation direction and magnitude in DM Mono.

### Recommendations
- **`RecommendationList.tsx`** — List of `<RecommendationCard>` items. Shows "X recommendations" count heading.
- **`RecommendationCard.tsx`** — Category label, description text, `<ConfidenceBadge>`, "Apply" button (calls `recommendationApi.applyRecommendation`). After applied: shows `formatDateTime(applied_at)` and outcome notes display. "Apply" button hidden after applied.
- **`RecommendationDetail.tsx`** — Full recommendation detail page. All fields + `<ApplyForm>` if not yet applied + outcome display after applied.
- **`ApplyForm.tsx`** — Inline form: notes textarea (optional). Submit calls `recommendationApi.applyRecommendation`. Shows confirmation after success.

### Advisories
- **`AdvisoryList.tsx`** — List of protocol advisories for a fermentation. Unacknowledged count badge.
- **`AdvisoryCard.tsx`** — Advisory type label, description, `formatRelative(created_at)`. Acknowledge button → `POST /advisories/{id}/acknowledge`. After acknowledged: shows timestamp, button hidden.

### Trigger
- **`TriggerAnalysisButton.tsx`** — Button that calls `analysisApi.triggerAnalysis`. Shows loading spinner during POST. On success: navigates to new analysis report. On error: shows `<ErrorMessage>`.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
