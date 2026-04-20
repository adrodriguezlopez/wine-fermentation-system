# Frontend Foundation — Iteration 1: Monorepo Scaffold + packages/ui

> **Source plan:** `docs/superpowers/plans/2026-04-18-frontend-foundation.md` (Tasks 1–5)  
> **Governing ADR:** [ADR-045](../../.ai-context/adr/ADR-045-frontend-architecture.md)  
> **Skills to load before starting:**  
> - `wine-frontend-context` → `.github/skills/wine-frontend-context/SKILL.md`  
> - `turborepo-monorepo` → `.github/skills/turborepo-monorepo/SKILL.md`

**Goal:** Bootstrap the Turborepo monorepo root and deliver a fully working `packages/ui` — zero React dependency, all tests green.

**Deliverable:** `packages/ui` exports Zod schemas, pure formatters, and constant maps. All tests pass (`pnpm test`). TypeScript strict with zero errors (`pnpm type-check`).

**Branch:** `feat/frontend-foundation-iteration-1`

---

## Pre-flight

- [ ] Read `.github/skills/wine-frontend-context/SKILL.md`
- [ ] Read `.github/skills/turborepo-monorepo/SKILL.md`
- [ ] Confirm on `main`, no uncommitted changes: `git status`
- [ ] Create branch: `git checkout -b feat/frontend-foundation-iteration-1`

---

## Task 1: Monorepo scaffold (root + Turborepo)

**Files to create:**
- `frontend/package.json`
- `frontend/pnpm-workspace.yaml`
- `frontend/turbo.json`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "wine-fermentation-frontend",
  "private": true,
  "packageManager": "pnpm@9.0.0",
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "type-check": "turbo run type-check"
  },
  "devDependencies": {
    "turbo": "^2.0.0",
    "typescript": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create `frontend/pnpm-workspace.yaml`**

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

- [ ] **Step 3: Create `frontend/turbo.json`**

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "type-check": {
      "dependsOn": ["^build"]
    },
    "lint": {}
  }
}
```

- [ ] **Step 4: Install and verify**

```bash
cd frontend
npm install -g turbo@latest
pnpm install
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/pnpm-workspace.yaml frontend/turbo.json
git commit -m "chore: bootstrap turborepo monorepo root"
```

---

## Task 2: packages/ui scaffold

**Files to create:**
- `frontend/packages/ui/package.json`
- `frontend/packages/ui/tsconfig.json`
- `frontend/packages/ui/vitest.config.ts`
- `frontend/packages/ui/__tests__/schemas.test.ts`

- [ ] **Step 1: Write failing test**

```typescript
// frontend/packages/ui/__tests__/schemas.test.ts
import { describe, it, expect } from 'vitest'
import { CreateFermentationSchema } from '../src/schemas/fermentation.schema'

describe('CreateFermentationSchema', () => {
  it('rejects missing vintage_year', () => {
    const result = CreateFermentationSchema.safeParse({
      yeast_strain: 'EC-1118',
      vessel_code: 'V-01',
      input_mass_kg: 5000,
      initial_sugar_brix: 22,
      start_date: '2026-04-01T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })

  it('accepts valid fermentation data', () => {
    const result = CreateFermentationSchema.safeParse({
      vintage_year: 2026,
      yeast_strain: 'EC-1118',
      vessel_code: 'V-01',
      input_mass_kg: 5000,
      initial_sugar_brix: 22,
      start_date: '2026-04-01T00:00:00Z',
    })
    expect(result.success).toBe(true)
  })
})
```

- [ ] **Step 2: Create `package.json`**

```json
{
  "name": "@wine/ui",
  "version": "0.0.1",
  "private": true,
  "main": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./schemas": "./src/schemas/index.ts",
    "./formatters": "./src/formatters/index.ts",
    "./constants": "./src/constants/index.ts"
  },
  "scripts": {
    "test": "vitest run",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "zod": "^3.23.0",
    "date-fns": "^3.6.0"
  },
  "devDependencies": {
    "vitest": "^1.6.0",
    "typescript": "^5.4.0"
  }
}
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*", "__tests__/**/*"]
}
```

- [ ] **Step 4: Create `vitest.config.ts`**

```typescript
// frontend/packages/ui/vitest.config.ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: { environment: 'node', globals: true },
})
```

- [ ] **Step 5: Run test to confirm it fails**

```bash
cd frontend/packages/ui && pnpm install && pnpm test
```

Expected: FAIL — `Cannot find module '../src/schemas/fermentation.schema'`

- [ ] **Step 6: Commit scaffold**

```bash
git add frontend/packages/ui/
git commit -m "chore: scaffold packages/ui with package.json, tsconfig, and failing tests"
```

---

## Task 3: packages/ui — Zod schemas

**Files to create:**
- `frontend/packages/ui/src/schemas/fermentation.schema.ts`
- `frontend/packages/ui/src/schemas/sample.schema.ts`
- `frontend/packages/ui/src/schemas/action.schema.ts`
- `frontend/packages/ui/src/schemas/protocol.schema.ts`
- `frontend/packages/ui/src/schemas/winery.schema.ts`
- `frontend/packages/ui/src/schemas/step-completion.schema.ts`
- `frontend/packages/ui/src/schemas/index.ts`

- [ ] **Step 1: Create `fermentation.schema.ts`**

```typescript
// frontend/packages/ui/src/schemas/fermentation.schema.ts
import { z } from 'zod'

const currentYear = new Date().getFullYear()

export const CreateFermentationSchema = z.object({
  vintage_year: z.number().int().min(1900).max(currentYear + 1),
  yeast_strain: z.string().min(1, 'Yeast strain is required'),
  vessel_code: z.string().min(1, 'Vessel code is required'),
  input_mass_kg: z.number().positive('Input mass must be positive'),
  initial_sugar_brix: z.number().min(0).max(50),
  initial_density: z.number().optional(),
  start_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
  notes: z.string().max(1000).optional(),
})

export const BlendFermentationSchema = CreateFermentationSchema.extend({
  lot_sources: z
    .array(
      z.object({
        harvest_lot_id: z.string().uuid(),
        percentage: z.number().min(0).max(100),
      })
    )
    .min(2, 'Blend must have at least 2 sources'),
})

export const UpdateFermentationSchema = CreateFermentationSchema.partial()

export type CreateFermentationData = z.infer<typeof CreateFermentationSchema>
export type BlendFermentationData = z.infer<typeof BlendFermentationSchema>
export type UpdateFermentationData = z.infer<typeof UpdateFermentationSchema>
```

- [ ] **Step 2: Create `sample.schema.ts`**

```typescript
// frontend/packages/ui/src/schemas/sample.schema.ts
import { z } from 'zod'

export const SAMPLE_TYPES = ['DENSITY', 'TEMPERATURE', 'BRIX', 'ACETIC_ACID'] as const
export type SampleType = typeof SAMPLE_TYPES[number]

export const SampleSchema = z.object({
  sample_type: z.enum(SAMPLE_TYPES),
  value: z.number({ required_error: 'Value is required' }),
  recorded_at: z.string().datetime({ message: 'Must be ISO datetime string' }),
  notes: z.string().max(500).optional(),
})

export type SampleFormData = z.infer<typeof SampleSchema>
```

- [ ] **Step 3: Create `action.schema.ts`**

```typescript
// frontend/packages/ui/src/schemas/action.schema.ts
import { z } from 'zod'

export const ACTION_TYPES = [
  'TEMPERATURE_ADJUSTMENT',
  'NUTRIENT_ADDITION',
  'PUMP_OVER',
  'INOCULATION',
  'PRESSING',
  'RACKING',
  'OTHER',
] as const
export type ActionType = typeof ACTION_TYPES[number]

export const ActionSchema = z.object({
  action_type: z.enum(ACTION_TYPES),
  description: z.string().min(10, 'Please describe the action taken (min 10 chars)'),
  taken_at: z.string().datetime({ message: 'Must be ISO datetime string' }),
  alert_id: z.string().uuid().optional(),
  recommendation_id: z.string().uuid().optional(),
})

export const UpdateActionOutcomeSchema = z.object({
  outcome: z.string().min(10, 'Please describe the outcome (min 10 chars)'),
})

export type ActionFormData = z.infer<typeof ActionSchema>
export type UpdateActionOutcomeData = z.infer<typeof UpdateActionOutcomeSchema>
```

- [ ] **Step 4: Create `protocol.schema.ts`**

```typescript
// frontend/packages/ui/src/schemas/protocol.schema.ts
import { z } from 'zod'

export const STEP_TYPES = [
  'INOCULATION',
  'TEMPERATURE_CHECK',
  'NUTRIENT_ADDITION',
  'PUMP_OVER',
  'DENSITY_CHECK',
  'PRESSING',
  'RACKING',
  'CLARIFICATION',
  'OTHER',
] as const

export const ProtocolSchema = z.object({
  varietal_code: z.string().min(1, 'Varietal code is required'),
  varietal_name: z.string().min(1, 'Varietal name is required'),
  version: z.string().regex(/^\d+\.\d+\.\d+$/, 'Must be semver format e.g. 1.0.0'),
  expected_duration_days: z.number().int().positive(),
  description: z.string().max(2000).optional(),
})

export const ProtocolStepSchema = z.object({
  step_type: z.enum(STEP_TYPES),
  sequence: z.number().int().positive(),
  duration_hours: z.number().positive(),
  threshold_values: z.record(z.number()).optional(),
  notes: z.string().max(1000).optional(),
})

export type ProtocolFormData = z.infer<typeof ProtocolSchema>
export type ProtocolStepFormData = z.infer<typeof ProtocolStepSchema>
```

- [ ] **Step 5: Create `winery.schema.ts` and `step-completion.schema.ts`**

```typescript
// frontend/packages/ui/src/schemas/winery.schema.ts
import { z } from 'zod'

export const WinerySchema = z.object({
  name: z.string().min(1, 'Winery name is required'),
  code: z.string().min(2).max(10).transform(s => s.toUpperCase()),
  location: z.string().optional(),
})

export type WineryFormData = z.infer<typeof WinerySchema>
```

```typescript
// frontend/packages/ui/src/schemas/step-completion.schema.ts
import { z } from 'zod'

export const StepCompletionSchema = z.object({
  completion_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
  notes: z.string().max(1000).optional(),
})

export type StepCompletionFormData = z.infer<typeof StepCompletionSchema>
```

- [ ] **Step 6: Create `schemas/index.ts`**

```typescript
// frontend/packages/ui/src/schemas/index.ts
export * from './fermentation.schema'
export * from './sample.schema'
export * from './action.schema'
export * from './protocol.schema'
export * from './winery.schema'
export * from './step-completion.schema'
```

- [ ] **Step 7: Run tests — expect PASS**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: PASS — 2 schema tests pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/packages/ui/src/schemas/
git commit -m "feat(ui): add Zod validation schemas for all domain entities"
```

---

## Task 4: packages/ui — Formatters

**Files to create:**
- `frontend/packages/ui/src/formatters/density.ts`
- `frontend/packages/ui/src/formatters/brix.ts`
- `frontend/packages/ui/src/formatters/temperature.ts`
- `frontend/packages/ui/src/formatters/units.ts`
- `frontend/packages/ui/src/formatters/date.ts`
- `frontend/packages/ui/src/formatters/deviation.ts`
- `frontend/packages/ui/src/formatters/index.ts`
- `frontend/packages/ui/__tests__/formatters.test.ts`

- [ ] **Step 1: Write failing formatter tests**

```typescript
// frontend/packages/ui/__tests__/formatters.test.ts
import { describe, it, expect } from 'vitest'
import { formatDensity, formatDensityShort } from '../src/formatters/density'
import { formatBrix } from '../src/formatters/brix'
import { formatCelsius } from '../src/formatters/temperature'
import { formatKg, formatDays, formatPercent } from '../src/formatters/units'
import { formatDeviationScore } from '../src/formatters/deviation'

describe('formatDensity', () => {
  it('formats to 4 decimal places with unit', () => {
    expect(formatDensity(1.0823)).toBe('1.0823 g/cm³')
  })
})

describe('formatDensityShort', () => {
  it('formats to 3 decimal places without unit', () => {
    expect(formatDensityShort(1.0823)).toBe('1.082')
  })
})

describe('formatBrix', () => {
  it('formats with °Bx unit', () => {
    expect(formatBrix(22.4)).toBe('22.4 °Bx')
  })
})

describe('formatCelsius', () => {
  it('formats with °C unit', () => {
    expect(formatCelsius(18.5)).toBe('18.5 °C')
  })
})

describe('formatKg', () => {
  it('formats with thousands separator', () => {
    expect(formatKg(5000)).toBe('5,000 kg')
  })
})

describe('formatDays', () => {
  it('formats day count', () => {
    expect(formatDays(14)).toBe('14 days')
    expect(formatDays(1)).toBe('1 day')
  })
})

describe('formatPercent', () => {
  it('converts fraction to percentage', () => {
    expect(formatPercent(0.87)).toBe('87%')
  })
})

describe('formatDeviationScore', () => {
  it('formats positive deviation with plus sign', () => {
    expect(formatDeviationScore(2.3)).toBe('+2.3σ')
  })
  it('formats negative deviation with minus sign', () => {
    expect(formatDeviationScore(-1.1)).toBe('−1.1σ')
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: FAIL — `Cannot find module '../src/formatters/density'`

- [ ] **Step 3: Create `density.ts`**

```typescript
export function formatDensity(value: number): string {
  return `${value.toFixed(4)} g/cm³`
}

export function formatDensityShort(value: number): string {
  return value.toFixed(3)
}
```

- [ ] **Step 4: Create `brix.ts`, `temperature.ts`, `units.ts`**

```typescript
// brix.ts
export function formatBrix(value: number): string {
  return `${value.toFixed(1)} °Bx`
}
```

```typescript
// temperature.ts
export function formatCelsius(value: number): string {
  return `${value.toFixed(1)} °C`
}
```

```typescript
// units.ts
export function formatKg(value: number): string {
  return `${value.toLocaleString('en-US')} kg`
}

export function formatDays(value: number): string {
  return `${value} ${value === 1 ? 'day' : 'days'}`
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}
```

- [ ] **Step 5: Create `date.ts`**

```typescript
// date.ts
import { formatDistanceToNow, format } from 'date-fns'

export function formatRelative(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return formatDistanceToNow(d, { addSuffix: true })
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, HH:mm')
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, yyyy')
}

export function formatDurationHours(hours: number): string {
  const days = Math.floor(hours / 24)
  const remaining = hours % 24
  if (days === 0) return `${remaining}h`
  if (remaining === 0) return `${days} day${days > 1 ? 's' : ''}`
  return `${days} day${days > 1 ? 's' : ''} ${remaining}h`
}
```

- [ ] **Step 6: Create `deviation.ts`**

```typescript
// deviation.ts
export function formatDeviationScore(score: number): string {
  const sign = score >= 0 ? '+' : '−'
  return `${sign}${Math.abs(score).toFixed(1)}σ`
}

export function formatDeviationSeverity(severity: string): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1).toLowerCase()
}
```

- [ ] **Step 7: Create `formatters/index.ts`**

```typescript
export * from './density'
export * from './brix'
export * from './temperature'
export * from './units'
export * from './date'
export * from './deviation'
```

- [ ] **Step 8: Run tests — expect PASS**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: PASS — all 10 formatter tests pass.

- [ ] **Step 9: Commit**

```bash
git add frontend/packages/ui/src/formatters/
git commit -m "feat(ui): add pure formatting functions for all measurement types"
```

---

## Task 5: packages/ui — Constants + root index

**Files to create:**
- `frontend/packages/ui/src/constants/fermentation-status.ts`
- `frontend/packages/ui/src/constants/confidence-levels.ts`
- `frontend/packages/ui/src/constants/alert-types.ts`
- `frontend/packages/ui/src/constants/sample-types.ts`
- `frontend/packages/ui/src/constants/recommendation-categories.ts`
- `frontend/packages/ui/src/constants/action-types.ts`
- `frontend/packages/ui/src/constants/index.ts`
- `frontend/packages/ui/src/index.ts`

- [ ] **Step 1: Create `fermentation-status.ts`**

```typescript
export type FermentationStatus = 'ACTIVE' | 'SLOW' | 'STUCK' | 'COMPLETED'

export const FERMENTATION_STATUS_LABEL: Record<FermentationStatus, string> = {
  ACTIVE: 'Active',
  SLOW: 'Slow',
  STUCK: 'Stuck',
  COMPLETED: 'Completed',
}

export const FERMENTATION_STATUS_COLOR: Record<FermentationStatus, string> = {
  ACTIVE: '#16A34A',
  SLOW: '#D97706',
  STUCK: '#DC2626',
  COMPLETED: '#6B7280',
}
```

- [ ] **Step 2: Create `confidence-levels.ts` and `alert-types.ts`**

```typescript
// confidence-levels.ts
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW'

export const CONFIDENCE_LABEL: Record<ConfidenceLevel, string> = {
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
}

export const CONFIDENCE_COLOR: Record<ConfidenceLevel, string> = {
  HIGH: '#16A34A',
  MEDIUM: '#D97706',
  LOW: '#DC2626',
}
```

```typescript
// alert-types.ts
export type AlertType =
  | 'TEMPERATURE_WARNING'
  | 'DENSITY_STALL'
  | 'PROTOCOL_DEVIATION'
  | 'STUCK_FERMENTATION'
  | 'HYDROGEN_SULFIDE_RISK'
  | 'DENSITY_DROP_TOO_FAST'

export type AlertStatus = 'PENDING' | 'ACKNOWLEDGED' | 'DISMISSED'

export const ALERT_TYPE_LABEL: Record<AlertType, string> = {
  TEMPERATURE_WARNING: 'Temperature Warning',
  DENSITY_STALL: 'Density Stall',
  PROTOCOL_DEVIATION: 'Protocol Deviation',
  STUCK_FERMENTATION: 'Stuck Fermentation',
  HYDROGEN_SULFIDE_RISK: 'H₂S Risk',
  DENSITY_DROP_TOO_FAST: 'Rapid Density Drop',
}

export const ALERT_STATUS_LABEL: Record<AlertStatus, string> = {
  PENDING: 'Pending',
  ACKNOWLEDGED: 'Acknowledged',
  DISMISSED: 'Dismissed',
}
```

- [ ] **Step 3: Create `sample-types.ts`, `recommendation-categories.ts`, `action-types.ts`**

```typescript
// sample-types.ts
export type SampleTypeKey = 'DENSITY' | 'TEMPERATURE' | 'BRIX' | 'ACETIC_ACID'

export const SAMPLE_TYPE_LABEL: Record<SampleTypeKey, string> = {
  DENSITY: 'Density',
  TEMPERATURE: 'Temperature',
  BRIX: 'Brix',
  ACETIC_ACID: 'Acetic Acid',
}

export const SAMPLE_TYPE_UNIT: Record<SampleTypeKey, string> = {
  DENSITY: 'g/cm³',
  TEMPERATURE: '°C',
  BRIX: '°Bx',
  ACETIC_ACID: 'g/L',
}
```

```typescript
// recommendation-categories.ts
export type RecommendationCategory = 'IMMEDIATE_ACTION' | 'MONITORING' | 'PREVENTIVE' | 'INFORMATIONAL'

export const RECOMMENDATION_CATEGORY_LABEL: Record<RecommendationCategory, string> = {
  IMMEDIATE_ACTION: 'Immediate Action',
  MONITORING: 'Monitor Closely',
  PREVENTIVE: 'Preventive',
  INFORMATIONAL: 'Info',
}

export const RECOMMENDATION_CATEGORY_COLOR: Record<RecommendationCategory, string> = {
  IMMEDIATE_ACTION: '#DC2626',
  MONITORING: '#D97706',
  PREVENTIVE: '#2563EB',
  INFORMATIONAL: '#6B7280',
}
```

```typescript
// action-types.ts
import { ACTION_TYPES, ActionType } from '../schemas/action.schema'

export const ACTION_TYPE_LABEL: Record<ActionType, string> = {
  TEMPERATURE_ADJUSTMENT: 'Temperature Adjustment',
  NUTRIENT_ADDITION: 'Nutrient Addition',
  PUMP_OVER: 'Pump Over',
  INOCULATION: 'Inoculation',
  PRESSING: 'Pressing',
  RACKING: 'Racking',
  OTHER: 'Other',
}
```

- [ ] **Step 4: Create `constants/index.ts` and root `src/index.ts`**

```typescript
// constants/index.ts
export * from './fermentation-status'
export * from './confidence-levels'
export * from './alert-types'
export * from './sample-types'
export * from './recommendation-categories'
export * from './action-types'
```

```typescript
// src/index.ts
export * from './schemas'
export * from './formatters'
export * from './constants'
```

- [ ] **Step 5: Run all tests**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: PASS — all tests pass.

- [ ] **Step 6: Type check**

```bash
cd frontend/packages/ui && pnpm type-check
```

Expected: zero TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/packages/ui/src/constants/ frontend/packages/ui/src/index.ts
git commit -m "feat(ui): add status/type constant maps for all domain enums"
```

---

## Verification checklist

- [ ] `cd frontend/packages/ui && pnpm test` — all tests pass (zero failures)
- [ ] `cd frontend/packages/ui && pnpm type-check` — zero TypeScript errors
- [ ] `packages/ui` has zero React imports anywhere (confirm with `grep -r "from 'react'" frontend/packages/ui/src`)
- [ ] All three exports work: schemas, formatters, constants

## Final commit

```bash
git add .
git commit -m "feat: complete frontend iteration 1 — monorepo scaffold + packages/ui"
```

---

## Handoff to Iteration 2

Iteration 2 (`2026-04-19-frontend-iteration-2-shared.md`) builds `packages/shared` on top of this.
Prerequisites before starting Iteration 2:
- This branch merged (or at minimum all tests green)
- `pnpm install` works from `frontend/`
- `@wine/ui` resolves correctly as a workspace dependency
