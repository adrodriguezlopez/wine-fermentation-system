# Component Context: Formatters (`packages/ui/src/formatters/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Pure formatting functions** that convert raw numeric or date values into human-readable strings. Used everywhere a measurement value is displayed — in chart tooltips, reading cards, tables, and mobile screens.

**Critical UI rule**: All numeric measurement values MUST be displayed using DM Mono font. Formatters return the string value; the calling component applies the font style.

## Architecture pattern

Pure functions — no side effects, no state, no React. Each function takes a raw value and returns a formatted string. Fully testable.

## Files

### `density.ts`
```typescript
// Fermentation density readings (g/cm³)
formatDensity(value: number): string  // e.g. 1.0823 → "1.0823 g/cm³"
formatDensityShort(value: number): string  // e.g. 1.0823 → "1.082"  (chart axis labels)
```

### `brix.ts`
```typescript
// Sugar content in degrees Brix
formatBrix(value: number): string  // e.g. 22.4 → "22.4 °Bx"
```

### `temperature.ts`
```typescript
// Fermentation temperature
formatCelsius(value: number): string  // e.g. 18.5 → "18.5 °C"
```

### `units.ts`
```typescript
formatKg(value: number): string       // e.g. 5000 → "5,000 kg"
formatDays(value: number): string     // e.g. 14 → "14 days"
formatPercent(value: number): string  // e.g. 0.87 → "87%"
```

### `date.ts`
```typescript
// Relative time for "freshness" display
formatRelative(date: string | Date): string  // e.g. "2 hours ago", "3 days ago"

// Absolute datetime for audit trails and protocol completion records
formatDateTime(date: string | Date): string  // e.g. "Apr 3, 09:00"
formatDate(date: string | Date): string      // e.g. "Apr 3, 2026"

// Duration display
formatDurationHours(hours: number): string   // e.g. 36 → "1 day 12h"
```

### `deviation.ts`
```typescript
// Analysis engine deviation scores
formatDeviationScore(score: number): string  // e.g. 2.3 → "+2.3σ", -1.1 → "−1.1σ"
formatDeviationSeverity(severity: string): string  // e.g. "HIGH" → "High"
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 1 / packages/ui
