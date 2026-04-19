# Component Context: Charts (`apps/web/src/components/charts/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Data visualization components** built on Recharts. The fermentation density trend chart is the centrepiece of the fermentation detail page — it's how admins track fermentation progression over time.

## Files

### `DensityLineChart.tsx`
Primary chart component. Renders a Recharts `LineChart` showing density readings over time for a single fermentation.

**Data source**: `GET /fermentations/{id}/samples` — array of `Sample` objects with `value`, `recorded_at`, `sample_type`.

**Visual spec**:
- X axis: datetime (formatted with `formatDate()` from `@ui/formatters`)
- Y axis: density values (formatted with `formatDensityShort()`)
- Line stroke: `#8B1A2E` (wine red), strokeWidth 2
- Dot: custom `<circle>` r=4, fill `#8B1A2E`, stroke white
- Grid: horizontal lines only, stroke `#E5E7EB`, strokeDasharray "4 4"
- Tooltip: custom — shows `formatDensity(value)` in DM Mono, `formatDateTime(recorded_at)`, sample_type label
- Responsive container: fills 100% width, fixed height 280px
- Loading state: shimmer skeleton same dimensions
- Empty state: placeholder message and icon when no samples exist

**Props**:
```typescript
interface DensityLineChartProps {
  samples: Sample[]
  isLoading?: boolean
}
```

### `StatCard.tsx`
Single metric display card. Used in the Overview tab for fermentation statistics.

```typescript
interface StatCardProps {
  label: string
  value: string | number     // formatted value, rendered in DM Mono
  unit?: string              // e.g. "days", "°C" — rendered smaller after value
  trend?: 'up' | 'down' | 'neutral'
  trendLabel?: string        // e.g. "vs last sample"
}
```

**Visual spec**:
- Card surface `#FFFFFF`, border `#E5E7EB`, border-radius `rounded-md`
- Label: DM Sans 12px muted `#6B7280`
- Value: DM Mono 28px `#1A1A2E`
- Trend indicator: small arrow icon in green (up) or red (down)

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
