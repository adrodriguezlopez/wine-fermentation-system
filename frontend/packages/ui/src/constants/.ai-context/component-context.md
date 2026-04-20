# Component Context: Constants (`packages/ui/src/constants/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Enum-to-display maps** for status labels, color tokens, and display names. Components never render raw enum strings like `'ACTIVE'` directly — they look up the human-readable label and color from these maps.

**Color token values** use hex strings (`'#16A34A'`) because this package is used in both Tailwind (web) and NativeWind (mobile). Each app maps the hex to a Tailwind class or NativeWind style at the component level — the constant simply provides the canonical color value.

## Architecture pattern

Plain TypeScript objects — `Record<EnumValue, string>`. No React.

## Files

### `fermentation-status.ts`
```typescript
export const FERMENTATION_STATUS_LABEL: Record<FermentationStatus, string> = {
  ACTIVE: 'Active',
  SLOW: 'Slow',
  STUCK: 'Stuck',
  COMPLETED: 'Completed',
}
export const FERMENTATION_STATUS_COLOR: Record<FermentationStatus, string> = {
  ACTIVE: '#16A34A',   // green
  SLOW: '#D97706',     // amber
  STUCK: '#DC2626',    // red
  COMPLETED: '#6B7280', // muted grey
}
```

### `confidence-levels.ts`
```typescript
export const CONFIDENCE_LABEL: Record<ConfidenceLevel, string> = {
  HIGH: 'High', MEDIUM: 'Medium', LOW: 'Low',
}
export const CONFIDENCE_COLOR: Record<ConfidenceLevel, string> = {
  HIGH: '#16A34A', MEDIUM: '#D97706', LOW: '#DC2626',
}
```

### `alert-types.ts`
```typescript
export const ALERT_TYPE_LABEL: Record<AlertType, string> = {
  TEMPERATURE_WARNING: 'Temperature Warning',
  DENSITY_STALL: 'Density Stall',
  PROTOCOL_DEVIATION: 'Protocol Deviation',
  // ...
}
export const ALERT_STATUS_LABEL: Record<AlertStatus, string> = {
  PENDING: 'Pending',
  ACKNOWLEDGED: 'Acknowledged',
  DISMISSED: 'Dismissed',
}
```

### `sample-types.ts`
```typescript
export const SAMPLE_TYPE_LABEL: Record<SampleType, string> = {
  DENSITY: 'Density', TEMPERATURE: 'Temperature', BRIX: 'Brix', PH: 'pH', SO2: 'SO₂', ...
}
export const SAMPLE_TYPE_UNIT: Record<SampleType, string> = {
  DENSITY: 'g/cm³', TEMPERATURE: '°C', BRIX: '°Bx', PH: '', SO2: 'mg/L', ...
}
```

### `recommendation-categories.ts`
```typescript
export const RECOMMENDATION_CATEGORY_LABEL: Record<RecommendationCategory, string> = {
  IMMEDIATE_ACTION: 'Immediate Action',
  MONITORING: 'Monitor Closely',
  PREVENTIVE: 'Preventive',
  INFORMATIONAL: 'Info',
}
```

### `action-types.ts`
```typescript
export const ACTION_TYPE_LABEL: Record<ActionType, string> = {
  TEMPERATURE_ADJUSTMENT: 'Temperature Adjustment',
  NUTRIENT_ADDITION: 'Nutrient Addition',
  PUMP_OVER: 'Pump Over',
  // ...
}
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 1 / packages/ui
