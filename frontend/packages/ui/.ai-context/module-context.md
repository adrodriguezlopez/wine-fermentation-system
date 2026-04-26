# Module Context: packages/ui

> **Parent Context**: See `frontend/.ai-context/project-context.md` for frontend-level decisions

## Module responsibility

**Shared non-visual building blocks** consumed by both `apps/web` and `apps/mobile`. Contains Zod validation schemas (same rules on both platforms), value formatters for measurement display, and constant maps for status labels and colors.

**What this is NOT**: This package does NOT contain React components or any rendering code. It is pure logic — schemas, functions, and constants. Adding a React component here would require it to work in both React DOM and React Native, which is impractical.

## Technology stack

- **Validation**: Zod v3 — form schemas with identical rules on web and mobile
- **Date formatting**: date-fns — locale-aware relative and absolute date display
- **Build**: tsup for dual CJS/ESM output

## Module interfaces

**Consumed by**: `apps/web` (forms, display) and `apps/mobile` (forms, display) via `@ui` path alias
**Depends on**: nothing (no dependencies on `packages/shared` or backend)

## Component structure

| Component | Path | Responsibility |
|-----------|------|---------------|
| Schemas | `src/schemas/` | Zod validation schemas for all create/update forms |
| Formatters | `src/formatters/` | Pure functions: measurement values → human-readable strings |
| Constants | `src/constants/` | Status label maps, color token maps, enum display maps |

## Key value proposition

Without this package, `SampleSchema` would be duplicated in `apps/web` and `apps/mobile`. A validation rule change (e.g. new sample type range) would need updating in two places. With this package, it's updated once and both apps get the fix.

## Implementation status

**Status**: ✅ FOUNDATION COMPLETE — Iteration 1 (2026-04-19)

**Delivered in foundation (Iteration 1):**
- `src/schemas/` — Zod v3 schemas: `CreateFermentationSchema`, `CreateSampleSchema`, `CreateProtocolSchema`, `CreateVineyardSchema`, `CreateHarvestLotSchema`, `LoginSchema`, and matching update schemas
- `src/formatters/` — pure functions: `formatDensity`, `formatBrix`, `formatTemperature`, `formatDays`, `formatDeviationScore`, `formatDate`, `formatRelativeDate`
- `src/constants/` — display maps: `FERMENTATION_STATUS_LABEL`, `FERMENTATION_STATUS_COLOR`, `SAMPLE_TYPE_LABEL`, `ALERT_SEVERITY_COLOR`, `ROLE_LABEL`
- Barrel exports via `src/index.ts`
- All tests run in Node environment (no jsdom needed)

## Component contexts

| Component | Context file |
|-----------|-------------|
| `src/schemas/` | `src/schemas/.ai-context/component-context.md` |
| `src/formatters/` | `src/formatters/.ai-context/component-context.md` |
| `src/constants/` | `src/constants/.ai-context/component-context.md` |
