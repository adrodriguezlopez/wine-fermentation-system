# Frontend Foundation Implementation Plan (Phases 0–2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the Turborepo monorepo from scratch, implement `packages/ui` (schemas/formatters/constants), `packages/shared` (API client + hooks), and scaffold `apps/web` with auth + routing — ready for screen implementation.

**Architecture:** Turborepo with pnpm workspaces hosts two apps (`web`, `mobile`) and two packages (`shared`, `ui`). `packages/ui` has zero React — pure Zod/date-fns. `packages/shared` has Axios + TanStack Query hooks that work in both Next.js and Expo. `apps/web` is Next.js 14 App Router with a dev proxy to 4 backend microservices.

**Tech Stack:** pnpm workspaces, Turborepo, Next.js 14 App Router, TanStack Query v5, Zustand, Shadcn/ui, Tailwind CSS, Axios, Vitest, React Testing Library, MSW

**Skills to load:** `wine-frontend-context`, `nextjs-app-router`, `tanstack-query-v5`, `shadcn-ui`, `turborepo-monorepo`

---

## File Structure

```
frontend/
├── package.json                         ← root workspace scripts
├── pnpm-workspace.yaml                  ← workspace package globs
├── turbo.json                           ← task pipeline
├── packages/
│   ├── ui/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── schemas/
│   │   │   │   ├── fermentation.schema.ts
│   │   │   │   ├── sample.schema.ts
│   │   │   │   ├── action.schema.ts
│   │   │   │   ├── protocol.schema.ts
│   │   │   │   ├── winery.schema.ts
│   │   │   │   ├── step-completion.schema.ts
│   │   │   │   └── index.ts
│   │   │   ├── formatters/
│   │   │   │   ├── density.ts
│   │   │   │   ├── brix.ts
│   │   │   │   ├── temperature.ts
│   │   │   │   ├── units.ts
│   │   │   │   ├── date.ts
│   │   │   │   ├── deviation.ts
│   │   │   │   └── index.ts
│   │   │   ├── constants/
│   │   │   │   ├── fermentation-status.ts
│   │   │   │   ├── confidence-levels.ts
│   │   │   │   ├── alert-types.ts
│   │   │   │   ├── sample-types.ts
│   │   │   │   ├── recommendation-categories.ts
│   │   │   │   ├── action-types.ts
│   │   │   │   └── index.ts
│   │   │   └── index.ts
│   │   └── __tests__/
│   │       ├── formatters.test.ts
│   │       └── schemas.test.ts
│   └── shared/
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── types/
│       │   │   ├── auth.ts
│       │   │   ├── fermentation.ts
│       │   │   ├── sample.ts
│       │   │   ├── protocol.ts
│       │   │   ├── analysis.ts
│       │   │   ├── alert.ts
│       │   │   ├── action.ts
│       │   │   ├── winery.ts
│       │   │   ├── vineyard.ts
│       │   │   └── index.ts
│       │   ├── api/
│       │   │   ├── client.ts            ← ApiClient class + AuthExpiredError
│       │   │   ├── fermentation.ts
│       │   │   ├── sample.ts
│       │   │   ├── protocol.ts
│       │   │   ├── protocol-steps.ts
│       │   │   ├── execution.ts
│       │   │   ├── step-completion.ts
│       │   │   ├── alert.ts
│       │   │   ├── action.ts
│       │   │   ├── analysis.ts
│       │   │   ├── recommendation.ts
│       │   │   ├── advisory.ts
│       │   │   ├── winery.ts
│       │   │   ├── vineyard.ts
│       │   │   ├── harvest-lot.ts
│       │   │   └── index.ts
│       │   ├── hooks/
│       │   │   ├── useAuth.ts
│       │   │   ├── useCurrentUser.ts
│       │   │   ├── useRole.ts
│       │   │   ├── usePolling.ts
│       │   │   ├── useStaleDataWarning.ts
│       │   │   └── index.ts
│       │   ├── storage/
│       │   │   ├── index.ts             ← TokenStorage interface
│       │   │   ├── cookie.ts            ← CookieTokenStorage (web)
│       │   │   └── secure-store.ts      ← SecureStoreTokenStorage (mobile)
│       │   ├── sync/
│       │   │   ├── sync-queue.ts        ← SyncQueue class
│       │   │   └── index.ts
│       │   └── index.ts
│       └── __tests__/
│           ├── client.test.ts
│           ├── useAuth.test.ts
│           └── usePolling.test.ts
└── apps/
    └── web/
        ├── package.json
        ├── tsconfig.json
        ├── next.config.ts               ← rewrites for dev proxy
        ├── tailwind.config.ts
        ├── src/
        │   ├── app/
        │   │   ├── layout.tsx           ← root: fonts + providers
        │   │   ├── page.tsx             ← redirect → /dashboard
        │   │   ├── 403/page.tsx
        │   │   ├── (auth)/
        │   │   │   └── login/page.tsx
        │   │   └── (dashboard)/
        │   │       ├── layout.tsx       ← sidebar + role guard
        │   │       └── dashboard/page.tsx  ← placeholder
        │   ├── providers/
        │   │   ├── query-provider.tsx
        │   │   └── auth-provider.tsx
        │   ├── lib/
        │   │   └── api-client.ts        ← singleton ApiClient for web
        │   ├── stores/
        │   │   └── auth.store.ts        ← Zustand auth state
        │   ├── components/
        │   │   └── layout/
        │   │       ├── sidebar.tsx
        │   │       ├── topbar.tsx
        │   │       └── admin-layout.tsx
        │   └── globals.css              ← CSS variables + Tailwind
        └── __tests__/
            ├── setup.ts
            └── login.test.tsx
```

---

## Task 1: Monorepo scaffold (root + Turborepo)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/pnpm-workspace.yaml`
- Create: `frontend/turbo.json`

- [ ] **Step 1: Create root package.json**

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

- [ ] **Step 2: Create pnpm-workspace.yaml**

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

- [ ] **Step 3: Create turbo.json**

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

- [ ] **Step 4: Install turbo globally and verify**

```bash
cd frontend
npm install -g turbo@latest
pnpm install
```

Expected: `node_modules/turbo` in root; no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/pnpm-workspace.yaml frontend/turbo.json
git commit -m "chore: bootstrap turborepo monorepo root"
```

---

## Task 2: packages/ui scaffold + package.json

**Files:**
- Create: `frontend/packages/ui/package.json`
- Create: `frontend/packages/ui/tsconfig.json`

- [ ] **Step 1: Write failing test for package structure**

Create `frontend/packages/ui/__tests__/schemas.test.ts`:

```typescript
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

- [ ] **Step 2: Create package.json**

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

- [ ] **Step 3: Create tsconfig.json**

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

- [ ] **Step 4: Run test to verify it fails**

```bash
cd frontend/packages/ui && pnpm install && pnpm test
```

Expected: FAIL — `Cannot find module '../src/schemas/fermentation.schema'`

- [ ] **Step 5: Commit scaffold**

```bash
git add frontend/packages/ui/
git commit -m "chore: scaffold packages/ui with package.json and failing tests"
```

---

## Task 3: packages/ui — Zod schemas

**Files:**
- Create: `frontend/packages/ui/src/schemas/fermentation.schema.ts`
- Create: `frontend/packages/ui/src/schemas/sample.schema.ts`
- Create: `frontend/packages/ui/src/schemas/action.schema.ts`
- Create: `frontend/packages/ui/src/schemas/protocol.schema.ts`
- Create: `frontend/packages/ui/src/schemas/winery.schema.ts`
- Create: `frontend/packages/ui/src/schemas/step-completion.schema.ts`
- Create: `frontend/packages/ui/src/schemas/index.ts`

- [ ] **Step 1: Create fermentation.schema.ts**

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

- [ ] **Step 2: Create sample.schema.ts**

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

- [ ] **Step 3: Create action.schema.ts**

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

- [ ] **Step 4: Create protocol.schema.ts**

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

- [ ] **Step 5: Create winery.schema.ts and step-completion.schema.ts**

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

- [ ] **Step 6: Create schemas/index.ts**

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

Expected: PASS — 2 tests pass (the failing-test and happy-path from Task 2)

- [ ] **Step 8: Commit**

```bash
git add frontend/packages/ui/src/schemas/
git commit -m "feat: add Zod validation schemas for all domain entities"
```

---

## Task 4: packages/ui — Formatters

**Files:**
- Create: `frontend/packages/ui/src/formatters/density.ts`
- Create: `frontend/packages/ui/src/formatters/brix.ts`
- Create: `frontend/packages/ui/src/formatters/temperature.ts`
- Create: `frontend/packages/ui/src/formatters/units.ts`
- Create: `frontend/packages/ui/src/formatters/date.ts`
- Create: `frontend/packages/ui/src/formatters/deviation.ts`
- Create: `frontend/packages/ui/src/formatters/index.ts`
- Create: `frontend/packages/ui/__tests__/formatters.test.ts`

- [ ] **Step 1: Write failing tests for formatters**

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

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: FAIL — `Cannot find module '../src/formatters/density'`

- [ ] **Step 3: Create density.ts**

```typescript
// frontend/packages/ui/src/formatters/density.ts
export function formatDensity(value: number): string {
  return `${value.toFixed(4)} g/cm³`
}

export function formatDensityShort(value: number): string {
  return value.toFixed(3)
}
```

- [ ] **Step 4: Create brix.ts, temperature.ts, units.ts**

```typescript
// frontend/packages/ui/src/formatters/brix.ts
export function formatBrix(value: number): string {
  return `${value.toFixed(1)} °Bx`
}
```

```typescript
// frontend/packages/ui/src/formatters/temperature.ts
export function formatCelsius(value: number): string {
  return `${value.toFixed(1)} °C`
}
```

```typescript
// frontend/packages/ui/src/formatters/units.ts
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

- [ ] **Step 5: Create date.ts**

```typescript
// frontend/packages/ui/src/formatters/date.ts
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

- [ ] **Step 6: Create deviation.ts**

```typescript
// frontend/packages/ui/src/formatters/deviation.ts
export function formatDeviationScore(score: number): string {
  const sign = score >= 0 ? '+' : '−'
  return `${sign}${Math.abs(score).toFixed(1)}σ`
}

export function formatDeviationSeverity(severity: string): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1).toLowerCase()
}
```

- [ ] **Step 7: Create formatters/index.ts**

```typescript
// frontend/packages/ui/src/formatters/index.ts
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

Expected: PASS — all 10 formatter tests pass

- [ ] **Step 9: Commit**

```bash
git add frontend/packages/ui/src/formatters/
git commit -m "feat: add pure formatting functions for all measurement types"
```

---

## Task 5: packages/ui — Constants

**Files:**
- Create: `frontend/packages/ui/src/constants/fermentation-status.ts`
- Create: `frontend/packages/ui/src/constants/confidence-levels.ts`
- Create: `frontend/packages/ui/src/constants/alert-types.ts`
- Create: `frontend/packages/ui/src/constants/sample-types.ts`
- Create: `frontend/packages/ui/src/constants/recommendation-categories.ts`
- Create: `frontend/packages/ui/src/constants/action-types.ts`
- Create: `frontend/packages/ui/src/constants/index.ts`
- Create: `frontend/packages/ui/src/index.ts`

- [ ] **Step 1: Create fermentation-status.ts**

```typescript
// frontend/packages/ui/src/constants/fermentation-status.ts
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

- [ ] **Step 2: Create confidence-levels.ts and alert-types.ts**

```typescript
// frontend/packages/ui/src/constants/confidence-levels.ts
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
// frontend/packages/ui/src/constants/alert-types.ts
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

- [ ] **Step 3: Create sample-types.ts, recommendation-categories.ts, action-types.ts**

```typescript
// frontend/packages/ui/src/constants/sample-types.ts
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
// frontend/packages/ui/src/constants/recommendation-categories.ts
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
// frontend/packages/ui/src/constants/action-types.ts
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

- [ ] **Step 4: Create constants/index.ts and root index.ts**

```typescript
// frontend/packages/ui/src/constants/index.ts
export * from './fermentation-status'
export * from './confidence-levels'
export * from './alert-types'
export * from './sample-types'
export * from './recommendation-categories'
export * from './action-types'
```

```typescript
// frontend/packages/ui/src/index.ts
export * from './schemas'
export * from './formatters'
export * from './constants'
```

- [ ] **Step 5: Run all tests**

```bash
cd frontend/packages/ui && pnpm test
```

Expected: PASS — all tests pass; zero TypeScript errors

- [ ] **Step 6: Type check**

```bash
cd frontend/packages/ui && pnpm type-check
```

Expected: zero errors

- [ ] **Step 7: Commit**

```bash
git add frontend/packages/ui/src/constants/ frontend/packages/ui/src/index.ts
git commit -m "feat: add status/type constant maps for all domain enums"
```

---

## Task 6: packages/shared — TypeScript types

**Files:**
- Create: `frontend/packages/shared/package.json`
- Create: `frontend/packages/shared/tsconfig.json`
- Create: `frontend/packages/shared/src/types/*.ts` (all type files)

- [ ] **Step 1: Write failing test for types**

Create `frontend/packages/shared/__tests__/types.test.ts`:

```typescript
import { describe, it, expectTypeOf } from 'vitest'
import type { FermentationDto, PaginatedResponse } from '../src/types/fermentation'
import type { UserDto } from '../src/types/auth'

describe('FermentationDto', () => {
  it('has required fields', () => {
    expectTypeOf<FermentationDto>().toHaveProperty('id')
    expectTypeOf<FermentationDto>().toHaveProperty('status')
    expectTypeOf<FermentationDto>().toHaveProperty('winery_id')
  })
})

describe('PaginatedResponse', () => {
  it('is generic', () => {
    type T = PaginatedResponse<FermentationDto>
    expectTypeOf<T>().toHaveProperty('items')
    expectTypeOf<T>().toHaveProperty('total')
  })
})

describe('UserDto', () => {
  it('has role and winery_id', () => {
    expectTypeOf<UserDto>().toHaveProperty('role')
    expectTypeOf<UserDto>().toHaveProperty('winery_id')
  })
})
```

- [ ] **Step 2: Create package.json**

```json
{
  "name": "@wine/shared",
  "version": "0.0.1",
  "private": true,
  "main": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./api": "./src/api/index.ts",
    "./hooks": "./src/hooks/index.ts",
    "./storage": "./src/storage/index.ts",
    "./sync": "./src/sync/index.ts",
    "./types": "./src/types/index.ts"
  },
  "scripts": {
    "test": "vitest run",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@wine/ui": "workspace:*",
    "axios": "^1.7.0",
    "@tanstack/react-query": "^5.40.0",
    "zustand": "^4.5.0",
    "js-cookie": "^3.0.5"
  },
  "devDependencies": {
    "vitest": "^1.6.0",
    "typescript": "^5.4.0",
    "@types/js-cookie": "^3.0.6",
    "react": "^18.3.0",
    "@types/react": "^18.3.0"
  },
  "peerDependencies": {
    "react": "^18.0.0"
  }
}
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "jsx": "react-jsx"
  },
  "include": ["src/**/*", "__tests__/**/*"]
}
```

- [ ] **Step 4: Create auth types**

```typescript
// frontend/packages/shared/src/types/auth.ts
export type UserRole = 'ADMIN' | 'WINEMAKER'

export interface UserDto {
  id: number
  email: string
  role: UserRole
  winery_id: string
}

export interface LoginResponseDto {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RefreshResponseDto {
  access_token: string
  token_type: 'bearer'
}
```

- [ ] **Step 5: Create fermentation types**

```typescript
// frontend/packages/shared/src/types/fermentation.ts
import type { FermentationStatus } from '@wine/ui/constants'

export interface FermentationDto {
  id: string
  winery_id: string
  vintage_year: number
  yeast_strain: string
  vessel_code: string
  input_mass_kg: number
  initial_sugar_brix: number
  initial_density: number | null
  start_date: string
  status: FermentationStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface FermentationStatisticsDto {
  days_fermenting: number
  current_density: number | null
  temperature_current: number | null
  density_drop_percent: number | null
  estimated_alcohol: number | null
}
```

- [ ] **Step 6: Create sample, protocol, analysis, alert, action, winery, vineyard types**

```typescript
// frontend/packages/shared/src/types/sample.ts
import type { SampleTypeKey } from '@wine/ui/constants'

export interface SampleDto {
  id: string
  fermentation_id: string
  sample_type: SampleTypeKey
  value: number
  recorded_at: string
  notes: string | null
  created_at: string
}
```

```typescript
// frontend/packages/shared/src/types/protocol.ts
export interface ProtocolDto {
  id: string
  winery_id: string
  varietal_code: string
  varietal_name: string
  version: string
  expected_duration_days: number
  description: string | null
  created_at: string
}

export interface ProtocolStepDto {
  id: string
  protocol_id: string
  step_type: string
  sequence: number
  duration_hours: number
  threshold_values: Record<string, number> | null
  notes: string | null
}

export interface ProtocolExecutionDto {
  id: string
  fermentation_id: string
  protocol_id: string
  status: 'ACTIVE' | 'COMPLETED' | 'ABANDONED'
  started_at: string
  completed_at: string | null
}

export interface StepCompletionDto {
  id: string
  execution_id: string
  step_id: string
  completed_by: number
  completion_date: string
  notes: string | null
}
```

```typescript
// frontend/packages/shared/src/types/alert.ts
import type { AlertType, AlertStatus } from '@wine/ui/constants'

export interface AlertDto {
  id: string
  execution_id: string
  alert_type: AlertType
  status: AlertStatus
  message: string
  created_at: string
  acknowledged_at: string | null
  dismissed_at: string | null
}
```

```typescript
// frontend/packages/shared/src/types/analysis.ts
import type { ConfidenceLevel } from '@wine/ui/constants'

export interface AnalysisDto {
  id: string
  fermentation_id: string
  winery_id: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  overall_confidence: ConfidenceLevel | null
  created_at: string
  completed_at: string | null
}

export interface AnomalyDto {
  id: string
  analysis_id: string
  anomaly_type: string
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  description: string
  detected_at: string
}

export interface RecommendationDto {
  id: string
  analysis_id: string
  category: string
  title: string
  description: string
  applied: boolean
  applied_at: string | null
}

export interface AdvisoryDto {
  id: string
  fermentation_id: string
  message: string
  acknowledged: boolean
  created_at: string
}
```

```typescript
// frontend/packages/shared/src/types/action.ts
import type { ActionType } from '@wine/ui/constants'

export interface ActionDto {
  id: string
  fermentation_id: string
  execution_id: string | null
  action_type: ActionType
  description: string
  taken_at: string
  outcome: string | null
  alert_id: string | null
  recommendation_id: string | null
}
```

```typescript
// frontend/packages/shared/src/types/winery.ts
export interface WineryDto {
  id: string
  name: string
  code: string
  location: string | null
  created_at: string
}
```

```typescript
// frontend/packages/shared/src/types/vineyard.ts
export interface VineyardDto {
  id: string
  winery_id: string
  name: string
  location: string | null
  hectares: number | null
  created_at: string
}

export interface HarvestLotDto {
  id: string
  vineyard_id: string
  vintage_year: number
  variety_name: string
  mass_kg: number
  harvest_date: string
  notes: string | null
}
```

- [ ] **Step 7: Create types/index.ts**

```typescript
// frontend/packages/shared/src/types/index.ts
export * from './auth'
export * from './fermentation'
export * from './sample'
export * from './protocol'
export * from './alert'
export * from './analysis'
export * from './action'
export * from './winery'
export * from './vineyard'
```

- [ ] **Step 8: Install dependencies and run tests**

```bash
cd frontend && pnpm install
cd packages/shared && pnpm test
```

Expected: PASS — type tests pass

- [ ] **Step 9: Commit**

```bash
git add frontend/packages/shared/
git commit -m "feat: add TypeScript DTO types matching all backend response shapes"
```

---

## Task 7: packages/shared — TokenStorage + ApiClient

**Files:**
- Create: `frontend/packages/shared/src/storage/index.ts`
- Create: `frontend/packages/shared/src/storage/cookie.ts`
- Create: `frontend/packages/shared/src/api/client.ts`
- Create: `frontend/packages/shared/__tests__/client.test.ts`

- [ ] **Step 1: Write failing test for ApiClient**

```typescript
// frontend/packages/shared/__tests__/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { ApiClient, AuthExpiredError } from '../src/api/client'
import type { TokenStorage } from '../src/storage/index'

const makeStorage = (accessToken: string | null = 'test-token'): TokenStorage => ({
  getAccessToken: vi.fn().mockResolvedValue(accessToken),
  setAccessToken: vi.fn().mockResolvedValue(undefined),
  getRefreshToken: vi.fn().mockResolvedValue('refresh-token'),
  setRefreshToken: vi.fn().mockResolvedValue(undefined),
  clear: vi.fn().mockResolvedValue(undefined),
})

describe('ApiClient', () => {
  it('can be instantiated with base URLs and storage', () => {
    const client = new ApiClient({
      baseURLs: {
        fermentation: 'http://localhost:8000',
        winery: 'http://localhost:8001',
        fruitOrigin: 'http://localhost:8002',
        analysis: 'http://localhost:8003',
      },
      tokenStorage: makeStorage(),
    })
    expect(client).toBeDefined()
    expect(client.fermentation).toBeDefined()
    expect(client.winery).toBeDefined()
    expect(client.fruitOrigin).toBeDefined()
    expect(client.analysis).toBeDefined()
  })

  it('exports AuthExpiredError', () => {
    expect(AuthExpiredError).toBeDefined()
    const err = new AuthExpiredError()
    expect(err).toBeInstanceOf(Error)
    expect(err.message).toBe('Authentication expired')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: FAIL — `Cannot find module '../src/api/client'`

- [ ] **Step 3: Create TokenStorage interface**

```typescript
// frontend/packages/shared/src/storage/index.ts
export interface TokenStorage {
  getAccessToken(): Promise<string | null>
  setAccessToken(token: string): Promise<void>
  getRefreshToken(): Promise<string | null>
  setRefreshToken(token: string): Promise<void>
  clear(): Promise<void>
}
```

- [ ] **Step 4: Create CookieTokenStorage (web)**

```typescript
// frontend/packages/shared/src/storage/cookie.ts
import Cookies from 'js-cookie'
import type { TokenStorage } from './index'

const ACCESS_TOKEN_KEY = 'wine_access_token'
const REFRESH_TOKEN_KEY = 'wine_refresh_token'

export class CookieTokenStorage implements TokenStorage {
  async getAccessToken(): Promise<string | null> {
    return Cookies.get(ACCESS_TOKEN_KEY) ?? null
  }

  async setAccessToken(token: string): Promise<void> {
    // Session cookie — expires when browser closes
    Cookies.set(ACCESS_TOKEN_KEY, token, { sameSite: 'strict' })
  }

  async getRefreshToken(): Promise<string | null> {
    return Cookies.get(REFRESH_TOKEN_KEY) ?? null
  }

  async setRefreshToken(token: string): Promise<void> {
    // 7-day expiry for refresh token
    Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7, sameSite: 'strict' })
  }

  async clear(): Promise<void> {
    Cookies.remove(ACCESS_TOKEN_KEY)
    Cookies.remove(REFRESH_TOKEN_KEY)
  }
}
```

- [ ] **Step 5: Create ApiClient**

```typescript
// frontend/packages/shared/src/api/client.ts
import axios, { type AxiosInstance, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import type { TokenStorage } from '../storage/index'
import type { LoginResponseDto, RefreshResponseDto, UserDto } from '../types/auth'

export class AuthExpiredError extends Error {
  constructor() {
    super('Authentication expired')
    this.name = 'AuthExpiredError'
  }
}

interface ApiClientConfig {
  baseURLs: {
    fermentation: string
    winery: string
    fruitOrigin: string
    analysis: string
  }
  tokenStorage: TokenStorage
}

export class ApiClient {
  public fermentation: AxiosInstance
  public winery: AxiosInstance
  public fruitOrigin: AxiosInstance
  public analysis: AxiosInstance

  private tokenStorage: TokenStorage
  private isRefreshing = false
  private refreshSubscribers: Array<(token: string) => void> = []

  constructor(config: ApiClientConfig) {
    this.tokenStorage = config.tokenStorage
    this.fermentation = this.createInstance(config.baseURLs.fermentation)
    this.winery = this.createInstance(config.baseURLs.winery)
    this.fruitOrigin = this.createInstance(config.baseURLs.fruitOrigin)
    this.analysis = this.createInstance(config.baseURLs.analysis)
  }

  private createInstance(baseURL: string): AxiosInstance {
    const instance = axios.create({ baseURL })

    // Inject Bearer token on every request
    instance.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
      const token = await this.tokenStorage.getAccessToken()
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    })

    // Handle 401 with auto-refresh
    instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue request to retry after refresh completes
            return new Promise((resolve, reject) => {
              this.refreshSubscribers.push((token) => {
                originalRequest.headers = { ...originalRequest.headers, Authorization: `Bearer ${token}` }
                originalRequest._retry = true
                resolve(instance(originalRequest))
              })
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const refreshToken = await this.tokenStorage.getRefreshToken()
            const response = await axios.post<RefreshResponseDto>(
              `${this.fermentation.defaults.baseURL}/api/v1/auth/refresh`,
              { refresh_token: refreshToken }
            )
            const newToken = response.data.access_token
            await this.tokenStorage.setAccessToken(newToken)

            // Flush queued requests
            this.refreshSubscribers.forEach((cb) => cb(newToken))
            this.refreshSubscribers = []
            this.isRefreshing = false

            originalRequest.headers = { ...originalRequest.headers, Authorization: `Bearer ${newToken}` }
            return instance(originalRequest)
          } catch (refreshError) {
            this.isRefreshing = false
            this.refreshSubscribers = []
            await this.tokenStorage.clear()
            throw new AuthExpiredError()
          }
        }
        return Promise.reject(error)
      }
    )

    return instance
  }

  // Auth endpoints (always use fermentation service base URL)
  async login(username: string, password: string): Promise<LoginResponseDto> {
    const response = await this.fermentation.post<LoginResponseDto>('/api/v1/auth/login', { username, password })
    await this.tokenStorage.setAccessToken(response.data.access_token)
    await this.tokenStorage.setRefreshToken(response.data.refresh_token)
    return response.data
  }

  async logout(): Promise<void> {
    await this.tokenStorage.clear()
  }

  async getCurrentUser(): Promise<UserDto> {
    const response = await this.fermentation.get<UserDto>('/api/v1/auth/me')
    return response.data
  }
}
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: PASS — 2 ApiClient tests pass

- [ ] **Step 7: Commit**

```bash
git add frontend/packages/shared/src/storage/ frontend/packages/shared/src/api/client.ts frontend/packages/shared/__tests__/client.test.ts
git commit -m "feat: add TokenStorage interface, CookieTokenStorage, and ApiClient with 401 auto-refresh"
```

---

## Task 8: packages/shared — API function files

**Files:**
- Create: `frontend/packages/shared/src/api/fermentation.ts`
- Create: `frontend/packages/shared/src/api/sample.ts`
- Create: `frontend/packages/shared/src/api/protocol.ts`
- Create: `frontend/packages/shared/src/api/protocol-steps.ts`
- Create: `frontend/packages/shared/src/api/execution.ts`
- Create: `frontend/packages/shared/src/api/step-completion.ts`
- Create: `frontend/packages/shared/src/api/alert.ts`
- Create: `frontend/packages/shared/src/api/action.ts`
- Create: `frontend/packages/shared/src/api/analysis.ts`
- Create: `frontend/packages/shared/src/api/recommendation.ts`
- Create: `frontend/packages/shared/src/api/advisory.ts`
- Create: `frontend/packages/shared/src/api/winery.ts`
- Create: `frontend/packages/shared/src/api/vineyard.ts`
- Create: `frontend/packages/shared/src/api/harvest-lot.ts`
- Create: `frontend/packages/shared/src/api/index.ts`

- [ ] **Step 1: Create fermentation.ts**

```typescript
// frontend/packages/shared/src/api/fermentation.ts
import type { ApiClient } from './client'
import type { FermentationDto, PaginatedResponse, FermentationStatisticsDto } from '../types/fermentation'
import type { CreateFermentationData, BlendFermentationData, UpdateFermentationData } from '@wine/ui/schemas'

export function createFermentationApi(client: ApiClient) {
  return {
    list(params?: { page?: number; size?: number; status?: string }): Promise<PaginatedResponse<FermentationDto>> {
      return client.fermentation.get('/api/v1/fermentations', { params }).then(r => r.data)
    },
    get(id: string): Promise<FermentationDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}`).then(r => r.data)
    },
    create(data: CreateFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations', data).then(r => r.data)
    },
    createBlend(data: BlendFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations/blends', data).then(r => r.data)
    },
    update(id: string, data: UpdateFermentationData): Promise<FermentationDto> {
      return client.fermentation.patch(`/api/v1/fermentations/${id}`, data).then(r => r.data)
    },
    complete(id: string): Promise<FermentationDto> {
      return client.fermentation.post(`/api/v1/fermentations/${id}/complete`).then(r => r.data)
    },
    getStatistics(id: string): Promise<FermentationStatisticsDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/statistics`).then(r => r.data)
    },
    getTimeline(id: string): Promise<unknown[]> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/timeline`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 2: Create sample.ts**

```typescript
// frontend/packages/shared/src/api/sample.ts
import type { ApiClient } from './client'
import type { SampleDto } from '../types/sample'
import type { SampleFormData } from '@wine/ui/schemas'

export function createSampleApi(client: ApiClient) {
  return {
    create(fermentationId: string, data: SampleFormData): Promise<SampleDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/samples`, data).then(r => r.data)
    },
    list(fermentationId: string): Promise<SampleDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/samples`).then(r => r.data)
    },
    getLatest(fermentationId: string): Promise<SampleDto | null> {
      return client.fermentation
        .get(`/api/v1/fermentations/${fermentationId}/samples/latest`)
        .then(r => r.data)
        .catch(() => null)
    },
  }
}
```

- [ ] **Step 3: Create alert.ts**

```typescript
// frontend/packages/shared/src/api/alert.ts
import type { ApiClient } from './client'
import type { AlertDto } from '../types/alert'

export function createAlertApi(client: ApiClient) {
  return {
    listForExecution(executionId: string): Promise<AlertDto[]> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/alerts`).then(r => r.data)
    },
    acknowledge(alertId: string): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/acknowledge`).then(r => r.data)
    },
    dismiss(alertId: string): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/dismiss`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 4: Create analysis.ts, recommendation.ts, advisory.ts**

```typescript
// frontend/packages/shared/src/api/analysis.ts
import type { ApiClient } from './client'
import type { AnalysisDto, AnomalyDto } from '../types/analysis'

export function createAnalysisApi(client: ApiClient) {
  return {
    trigger(fermentationId: string): Promise<AnalysisDto> {
      return client.analysis.post('/api/v1/analyses', { fermentation_id: fermentationId }).then(r => r.data)
    },
    get(id: string): Promise<AnalysisDto> {
      return client.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<AnalysisDto[]> {
      return client.analysis.get(`/api/v1/analyses/fermentation/${fermentationId}`).then(r => r.data)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/recommendation.ts
import type { ApiClient } from './client'
import type { RecommendationDto } from '../types/analysis'

export function createRecommendationApi(client: ApiClient) {
  return {
    get(id: string): Promise<RecommendationDto> {
      return client.analysis.get(`/api/v1/recommendations/${id}`).then(r => r.data)
    },
    apply(id: string): Promise<RecommendationDto> {
      return client.analysis.put(`/api/v1/recommendations/${id}/apply`).then(r => r.data)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/advisory.ts
import type { ApiClient } from './client'
import type { AdvisoryDto } from '../types/analysis'

export function createAdvisoryApi(client: ApiClient) {
  return {
    listForFermentation(fermentationId: string): Promise<AdvisoryDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/advisories`).then(r => r.data)
    },
    acknowledge(id: string): Promise<AdvisoryDto> {
      return client.analysis.post(`/api/v1/advisories/${id}/acknowledge`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 5: Create protocol.ts, protocol-steps.ts, execution.ts, step-completion.ts, action.ts**

```typescript
// frontend/packages/shared/src/api/protocol.ts
import type { ApiClient } from './client'
import type { ProtocolDto } from '../types/protocol'
import type { ProtocolFormData } from '@wine/ui/schemas'

export function createProtocolApi(client: ApiClient) {
  return {
    list(): Promise<ProtocolDto[]> {
      return client.fermentation.get('/api/v1/protocols').then(r => r.data)
    },
    get(id: string): Promise<ProtocolDto> {
      return client.fermentation.get(`/api/v1/protocols/${id}`).then(r => r.data)
    },
    create(data: ProtocolFormData): Promise<ProtocolDto> {
      return client.fermentation.post('/api/v1/protocols', data).then(r => r.data)
    },
    update(id: string, data: Partial<ProtocolFormData>): Promise<ProtocolDto> {
      return client.fermentation.patch(`/api/v1/protocols/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${id}`).then(() => undefined)
    },
    clone(id: string): Promise<ProtocolDto> {
      return client.fermentation.post(`/api/v1/protocols/${id}/clone`).then(r => r.data)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/protocol-steps.ts
import type { ApiClient } from './client'
import type { ProtocolStepDto } from '../types/protocol'
import type { ProtocolStepFormData } from '@wine/ui/schemas'

export function createProtocolStepsApi(client: ApiClient) {
  return {
    list(protocolId: string): Promise<ProtocolStepDto[]> {
      return client.fermentation.get(`/api/v1/protocols/${protocolId}/steps`).then(r => r.data)
    },
    add(protocolId: string, data: ProtocolStepFormData): Promise<ProtocolStepDto> {
      return client.fermentation.post(`/api/v1/protocols/${protocolId}/steps`, data).then(r => r.data)
    },
    update(protocolId: string, stepId: string, data: Partial<ProtocolStepFormData>): Promise<ProtocolStepDto> {
      return client.fermentation.patch(`/api/v1/protocols/${protocolId}/steps/${stepId}`, data).then(r => r.data)
    },
    delete(protocolId: string, stepId: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${protocolId}/steps/${stepId}`).then(() => undefined)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/execution.ts
import type { ApiClient } from './client'
import type { ProtocolExecutionDto } from '../types/protocol'

export function createExecutionApi(client: ApiClient) {
  return {
    start(fermentationId: string, protocolId: string): Promise<ProtocolExecutionDto> {
      return client.fermentation
        .post(`/api/v1/fermentations/${fermentationId}/execute`, { protocol_id: protocolId })
        .then(r => r.data)
    },
    get(id: string): Promise<ProtocolExecutionDto> {
      return client.fermentation.get(`/api/v1/executions/${id}`).then(r => r.data)
    },
    list(): Promise<ProtocolExecutionDto[]> {
      return client.fermentation.get('/api/v1/executions').then(r => r.data)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/step-completion.ts
import type { ApiClient } from './client'
import type { StepCompletionDto } from '../types/protocol'
import type { StepCompletionFormData } from '@wine/ui/schemas'

export function createStepCompletionApi(client: ApiClient) {
  return {
    complete(executionId: string, data: StepCompletionFormData): Promise<StepCompletionDto> {
      return client.fermentation.post(`/api/v1/executions/${executionId}/complete`, data).then(r => r.data)
    },
    list(executionId: string): Promise<StepCompletionDto[]> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/completions`).then(r => r.data)
    },
    get(id: string): Promise<StepCompletionDto> {
      return client.fermentation.get(`/api/v1/completions/${id}`).then(r => r.data)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/action.ts
import type { ApiClient } from './client'
import type { ActionDto } from '../types/action'
import type { ActionFormData, UpdateActionOutcomeData } from '@wine/ui/schemas'

export function createActionApi(client: ApiClient) {
  return {
    create(fermentationId: string, data: ActionFormData): Promise<ActionDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/actions`, data).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<ActionDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/actions`).then(r => r.data)
    },
    updateOutcome(id: string, data: UpdateActionOutcomeData): Promise<ActionDto> {
      return client.fermentation.patch(`/api/v1/actions/${id}/outcome`, data).then(r => r.data)
    },
  }
}
```

- [ ] **Step 6: Create winery.ts, vineyard.ts, harvest-lot.ts**

```typescript
// frontend/packages/shared/src/api/winery.ts
import type { ApiClient } from './client'
import type { WineryDto } from '../types/winery'
import type { WineryFormData } from '@wine/ui/schemas'

export function createWineryApi(client: ApiClient) {
  return {
    list(): Promise<WineryDto[]> {
      return client.winery.get('/api/v1/admin/wineries').then(r => r.data)
    },
    get(id: string): Promise<WineryDto> {
      return client.winery.get(`/api/v1/admin/wineries/${id}`).then(r => r.data)
    },
    create(data: WineryFormData): Promise<WineryDto> {
      return client.winery.post('/api/v1/admin/wineries', data).then(r => r.data)
    },
    update(id: string, data: Partial<WineryFormData>): Promise<WineryDto> {
      return client.winery.patch(`/api/v1/admin/wineries/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.winery.delete(`/api/v1/admin/wineries/${id}`).then(() => undefined)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/vineyard.ts
import type { ApiClient } from './client'
import type { VineyardDto } from '../types/vineyard'

export function createVineyardApi(client: ApiClient) {
  return {
    list(): Promise<VineyardDto[]> {
      return client.fruitOrigin.get('/api/v1/vineyards/').then(r => r.data)
    },
    get(id: string): Promise<VineyardDto> {
      return client.fruitOrigin.get(`/api/v1/vineyards/${id}`).then(r => r.data)
    },
    create(data: { name: string; location?: string; hectares?: number }): Promise<VineyardDto> {
      return client.fruitOrigin.post('/api/v1/vineyards/', data).then(r => r.data)
    },
    update(id: string, data: Partial<{ name: string; location: string; hectares: number }>): Promise<VineyardDto> {
      return client.fruitOrigin.patch(`/api/v1/vineyards/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fruitOrigin.delete(`/api/v1/vineyards/${id}`).then(() => undefined)
    },
  }
}
```

```typescript
// frontend/packages/shared/src/api/harvest-lot.ts
import type { ApiClient } from './client'
import type { HarvestLotDto } from '../types/vineyard'

export function createHarvestLotApi(client: ApiClient) {
  return {
    list(vineyardId?: string): Promise<HarvestLotDto[]> {
      return client.fruitOrigin.get('/api/v1/harvest-lots/', { params: vineyardId ? { vineyard_id: vineyardId } : {} }).then(r => r.data)
    },
    get(id: string): Promise<HarvestLotDto> {
      return client.fruitOrigin.get(`/api/v1/harvest-lots/${id}`).then(r => r.data)
    },
    create(data: { vineyard_id: string; vintage_year: number; variety_name: string; mass_kg: number; harvest_date: string; notes?: string }): Promise<HarvestLotDto> {
      return client.fruitOrigin.post('/api/v1/harvest-lots/', data).then(r => r.data)
    },
  }
}
```

- [ ] **Step 7: Create api/index.ts**

```typescript
// frontend/packages/shared/src/api/index.ts
export { ApiClient, AuthExpiredError } from './client'
export { createFermentationApi } from './fermentation'
export { createSampleApi } from './sample'
export { createProtocolApi } from './protocol'
export { createProtocolStepsApi } from './protocol-steps'
export { createExecutionApi } from './execution'
export { createStepCompletionApi } from './step-completion'
export { createAlertApi } from './alert'
export { createActionApi } from './action'
export { createAnalysisApi } from './analysis'
export { createRecommendationApi } from './recommendation'
export { createAdvisoryApi } from './advisory'
export { createWineryApi } from './winery'
export { createVineyardApi } from './vineyard'
export { createHarvestLotApi } from './harvest-lot'
```

- [ ] **Step 8: Run tests and type-check**

```bash
cd frontend/packages/shared && pnpm test && pnpm type-check
```

Expected: PASS — all tests pass, zero TypeScript errors

- [ ] **Step 9: Commit**

```bash
git add frontend/packages/shared/src/api/
git commit -m "feat: add typed API functions for all backend endpoints"
```

---

## Task 9: packages/shared — Auth hooks + Zustand store

**Files:**
- Create: `frontend/packages/shared/src/hooks/useAuth.ts`
- Create: `frontend/packages/shared/src/hooks/useCurrentUser.ts`
- Create: `frontend/packages/shared/src/hooks/useRole.ts`
- Create: `frontend/packages/shared/src/hooks/usePolling.ts`
- Create: `frontend/packages/shared/src/hooks/useStaleDataWarning.ts`
- Create: `frontend/packages/shared/src/hooks/index.ts`
- Create: `frontend/packages/shared/__tests__/useAuth.test.ts`

- [ ] **Step 1: Write failing test for useAuth**

```typescript
// frontend/packages/shared/__tests__/useAuth.test.ts
import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'

// We need to test useAuth in isolation — mock the ApiClient
vi.mock('../src/api/client', () => ({
  ApiClient: vi.fn(),
  AuthExpiredError: class AuthExpiredError extends Error { constructor() { super('expired') } },
}))

// Minimal test: hook exists and exports expected shape
describe('useAuth module', () => {
  it('exports useAuth function', async () => {
    const mod = await import('../src/hooks/useAuth')
    expect(typeof mod.useAuth).toBe('function')
  })
})

describe('useRole module', () => {
  it('exports useRole function', async () => {
    const mod = await import('../src/hooks/useRole')
    expect(typeof mod.useRole).toBe('function')
  })
})

describe('usePolling module', () => {
  it('exports usePolling function', async () => {
    const mod = await import('../src/hooks/usePolling')
    expect(typeof mod.usePolling).toBe('function')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: FAIL — `Cannot find module '../src/hooks/useAuth'`

- [ ] **Step 3: Create useCurrentUser.ts**

```typescript
// frontend/packages/shared/src/hooks/useCurrentUser.ts
import { useQuery } from '@tanstack/react-query'
import type { UserDto } from '../types/auth'
import type { ApiClient } from '../api/client'

// ApiClient is passed via context in each app — this hook requires it as a parameter
// to avoid a global singleton that reads process.env
export function makeUseCurrentUser(client: ApiClient) {
  return function useCurrentUser() {
    return useQuery<UserDto>({
      queryKey: ['currentUser'],
      queryFn: () => client.getCurrentUser(),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })
  }
}
```

- [ ] **Step 4: Create useRole.ts**

```typescript
// frontend/packages/shared/src/hooks/useRole.ts
import type { UserRole } from '../types/auth'

// Called with the result of useCurrentUser()
export function useRole(role: UserRole | undefined) {
  return {
    role,
    isAdmin: role === 'ADMIN',
    isWinemaker: role === 'WINEMAKER',
    hasRole: (r: UserRole) => role === r,
  }
}
```

- [ ] **Step 5: Create usePolling.ts**

```typescript
// frontend/packages/shared/src/hooks/usePolling.ts
import { useQuery, type QueryKey } from '@tanstack/react-query'

interface UsePollingOptions {
  intervalMs?: number
  enabled?: boolean
}

export function usePolling<T>(
  queryKey: QueryKey,
  queryFn: () => Promise<T>,
  options: UsePollingOptions = {}
) {
  const { intervalMs = 30_000, enabled = true } = options

  return useQuery<T>({
    queryKey,
    queryFn,
    refetchInterval: enabled ? intervalMs : false,
    refetchIntervalInBackground: false,
    enabled,
  })
}
```

- [ ] **Step 6: Create useStaleDataWarning.ts**

```typescript
// frontend/packages/shared/src/hooks/useStaleDataWarning.ts
import { useQueryClient, type QueryKey } from '@tanstack/react-query'

const STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000 // 4 hours

export function useStaleDataWarning(queryKey: QueryKey) {
  const queryClient = useQueryClient()
  const state = queryClient.getQueryState(queryKey as string[])

  if (!state?.dataUpdatedAt) {
    return { isStale: false, staleSinceMinutes: 0 }
  }

  const ageMins = (Date.now() - state.dataUpdatedAt) / 60_000
  const isStale = Date.now() - state.dataUpdatedAt > STALE_THRESHOLD_MS

  return { isStale, staleSinceMinutes: Math.round(ageMins) }
}
```

- [ ] **Step 7: Create useAuth.ts**

```typescript
// frontend/packages/shared/src/hooks/useAuth.ts
import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { ApiClient, AuthExpiredError } from '../api/client'

// Factory — each app calls makeUseAuth(client) once to get a bound hook
export function makeUseAuth(client: ApiClient) {
  return function useAuth() {
    const queryClient = useQueryClient()

    const login = useCallback(async (username: string, password: string) => {
      await client.login(username, password)
      // Invalidate currentUser so it refetches with the new token
      await queryClient.invalidateQueries({ queryKey: ['currentUser'] })
    }, [queryClient])

    const logout = useCallback(async () => {
      await client.logout()
      queryClient.clear()
    }, [queryClient])

    return { login, logout }
  }
}
```

- [ ] **Step 8: Create hooks/index.ts**

```typescript
// frontend/packages/shared/src/hooks/index.ts
export { makeUseAuth } from './useAuth'
export { makeUseCurrentUser } from './useCurrentUser'
export { useRole } from './useRole'
export { usePolling } from './usePolling'
export { useStaleDataWarning } from './useStaleDataWarning'
```

- [ ] **Step 9: Create shared/src/index.ts**

```typescript
// frontend/packages/shared/src/index.ts
export * from './types'
export * from './api'
export * from './hooks'
export * from './storage'
```

- [ ] **Step 10: Run all tests**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: PASS — all tests pass (including the new useAuth/useRole/usePolling existence tests)

- [ ] **Step 11: Commit**

```bash
git add frontend/packages/shared/src/hooks/ frontend/packages/shared/src/index.ts frontend/packages/shared/__tests__/useAuth.test.ts
git commit -m "feat: add auth hooks, polling hook, and stale data warning hook"
```

---

## Task 10: apps/web scaffold — Next.js + Tailwind + Shadcn/ui

**Files:**
- Create: `frontend/apps/web/package.json`
- Create: `frontend/apps/web/tsconfig.json`
- Create: `frontend/apps/web/next.config.ts`
- Create: `frontend/apps/web/tailwind.config.ts`
- Create: `frontend/apps/web/src/app/globals.css`
- Create: `frontend/apps/web/src/app/layout.tsx`

- [ ] **Step 1: Write failing test for web scaffold**

Create `frontend/apps/web/__tests__/setup.ts` and `login.test.tsx`:

```typescript
// frontend/apps/web/__tests__/setup.ts
import '@testing-library/jest-dom'
```

```tsx
// frontend/apps/web/__tests__/login.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

// Minimal test — just verify the test infrastructure works
describe('login page test infrastructure', () => {
  it('renders basic html', () => {
    render(<div data-testid="test">Hello</div>)
    expect(screen.getByTestId('test')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Create package.json**

```json
{
  "name": "@wine/web",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@wine/shared": "workspace:*",
    "@wine/ui": "workspace:*",
    "@tanstack/react-query": "^5.40.0",
    "@tanstack/react-query-devtools": "^5.40.0",
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "js-cookie": "^3.0.5",
    "lucide-react": "^0.400.0",
    "recharts": "^2.12.0",
    "framer-motion": "^11.0.0",
    "react-hook-form": "^7.52.0",
    "@hookform/resolvers": "^3.6.0",
    "zod": "^3.23.0",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "class-variance-authority": "^0.7.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/js-cookie": "^3.0.6",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.6.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/user-event": "^14.5.0",
    "msw": "^2.3.0",
    "jsdom": "^24.0.0"
  }
}
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"],
      "@wine/shared": ["../../packages/shared/src/index.ts"],
      "@wine/ui": ["../../packages/ui/src/index.ts"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create next.config.ts**

```typescript
// frontend/apps/web/next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    // Development only: proxy API calls to backend microservices
    return [
      {
        source: '/api/fermentation/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
      {
        source: '/api/winery/:path*',
        destination: 'http://localhost:8001/api/v1/:path*',
      },
      {
        source: '/api/fruit-origin/:path*',
        destination: 'http://localhost:8002/api/v1/:path*',
      },
      {
        source: '/api/analysis/:path*',
        destination: 'http://localhost:8003/api/v1/:path*',
      },
    ]
  },
}

export default nextConfig
```

- [ ] **Step 5: Create tailwind.config.ts**

```typescript
// frontend/apps/web/tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Cormorant Garamond', 'serif'],
        mono: ['DM Mono', 'monospace'],
        sans: ['DM Sans', 'sans-serif'],
      },
      colors: {
        background: '#FAFAF8',
        surface: '#FFFFFF',
        'text-primary': '#1A1A2E',
        accent: '#8B1A2E',
        muted: '#6B7280',
        success: '#16A34A',
        warning: '#D97706',
        danger: '#DC2626',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
```

- [ ] **Step 6: Create globals.css**

```css
/* frontend/apps/web/src/app/globals.css */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 60 33% 98%;
    --foreground: 240 30% 14%;
    --card: 0 0% 100%;
    --card-foreground: 240 30% 14%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 30% 14%;
    --primary: 350 69% 32%;
    --primary-foreground: 0 0% 100%;
    --secondary: 60 5% 96%;
    --secondary-foreground: 240 30% 14%;
    --muted: 60 5% 96%;
    --muted-foreground: 220 9% 46%;
    --accent: 60 5% 96%;
    --accent-foreground: 240 30% 14%;
    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 100%;
    --border: 60 7% 91%;
    --input: 60 7% 91%;
    --ring: 350 69% 32%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground font-sans;
  }
}
```

- [ ] **Step 7: Create root layout.tsx**

```tsx
// frontend/apps/web/src/app/layout.tsx
import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'

export const metadata: Metadata = {
  title: 'Wine Fermentation System',
  description: 'Fermentation monitoring dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  )
}
```

- [ ] **Step 8: Install deps and add Shadcn/ui**

```bash
cd frontend && pnpm install
cd apps/web && npx shadcn@latest init --defaults
# When prompted: style=Default, base color=Neutral, CSS variables=yes
npx shadcn@latest add button card badge input label select table dialog sheet form
```

- [ ] **Step 9: Run test**

```bash
cd frontend/apps/web && pnpm test
```

Expected: PASS — 1 test passes

- [ ] **Step 10: Commit**

```bash
git add frontend/apps/web/
git commit -m "feat: scaffold apps/web with Next.js 14, Tailwind, Shadcn/ui"
```

---

## Task 11: apps/web — Providers, ApiClient singleton, Zustand auth store

**Files:**
- Create: `frontend/apps/web/src/providers/query-provider.tsx`
- Create: `frontend/apps/web/src/providers/auth-provider.tsx`
- Create: `frontend/apps/web/src/lib/api-client.ts`
- Create: `frontend/apps/web/src/stores/auth.store.ts`

- [ ] **Step 1: Write failing test for auth store**

```tsx
// frontend/apps/web/__tests__/auth-store.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../src/stores/auth.store'

describe('auth store', () => {
  beforeEach(() => {
    useAuthStore.getState().setUser(null)
  })

  it('starts with null user', () => {
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('can set user', () => {
    useAuthStore.getState().setUser({ id: 1, email: 'a@b.com', role: 'WINEMAKER', winery_id: 'w-1' })
    expect(useAuthStore.getState().user?.email).toBe('a@b.com')
  })

  it('can clear user', () => {
    useAuthStore.getState().setUser({ id: 1, email: 'a@b.com', role: 'WINEMAKER', winery_id: 'w-1' })
    useAuthStore.getState().setUser(null)
    expect(useAuthStore.getState().user).toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend/apps/web && pnpm test
```

Expected: FAIL — `Cannot find module '../src/stores/auth.store'`

- [ ] **Step 3: Create Zustand auth store**

```typescript
// frontend/apps/web/src/stores/auth.store.ts
import { create } from 'zustand'
import type { UserDto } from '@wine/shared'

interface AuthState {
  user: UserDto | null
  setUser: (user: UserDto | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}))
```

- [ ] **Step 4: Create api-client singleton**

```typescript
// frontend/apps/web/src/lib/api-client.ts
import { ApiClient } from '@wine/shared'
import { CookieTokenStorage } from '@wine/shared/storage/cookie'

const tokenStorage = new CookieTokenStorage()

export const apiClient = new ApiClient({
  baseURLs: {
    fermentation: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000/api/fermentation',
    winery: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000/api/winery',
    fruitOrigin: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000/api/fruit-origin',
    analysis: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000/api/analysis',
  },
  tokenStorage,
})
```

- [ ] **Step 5: Create QueryProvider**

```tsx
// frontend/apps/web/src/providers/query-provider.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
```

- [ ] **Step 6: Create AuthProvider**

```tsx
// frontend/apps/web/src/providers/auth-provider.tsx
'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth.store'
import { apiClient } from '@/lib/api-client'
import { AuthExpiredError } from '@wine/shared'
import { useRouter } from 'next/navigation'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const setUser = useAuthStore(state => state.setUser)
  const router = useRouter()

  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: () => apiClient.getCurrentUser(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  useEffect(() => {
    setUser(user ?? null)
  }, [user, setUser])

  return <>{children}</>
}
```

- [ ] **Step 7: Run tests**

```bash
cd frontend/apps/web && pnpm test
```

Expected: PASS — all 4 tests pass (3 auth store tests + 1 render test)

- [ ] **Step 8: Commit**

```bash
git add frontend/apps/web/src/providers/ frontend/apps/web/src/lib/ frontend/apps/web/src/stores/ frontend/apps/web/__tests__/auth-store.test.ts
git commit -m "feat: add QueryProvider, AuthProvider, ApiClient singleton, Zustand auth store"
```

---

## Task 12: apps/web — Login page

**Files:**
- Create: `frontend/apps/web/src/app/(auth)/login/page.tsx`
- Create: `frontend/apps/web/src/app/page.tsx`
- Create: `frontend/apps/web/src/app/403/page.tsx`
- Modify: `frontend/apps/web/__tests__/login.test.tsx`

- [ ] **Step 1: Write login page test**

```tsx
// frontend/apps/web/__tests__/login.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from '../src/app/(auth)/login/page'

// Mock router
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

// Mock apiClient
vi.mock('../src/lib/api-client', () => ({
  apiClient: {
    login: vi.fn().mockResolvedValue({ access_token: 'tok', refresh_token: 'ref', token_type: 'bearer' }),
    getCurrentUser: vi.fn().mockResolvedValue({ id: 1, email: 'test@test.com', role: 'ADMIN', winery_id: 'w-1' }),
  },
}))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
)

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    render(<LoginPage />, { wrapper })
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('renders sign in button', () => {
    render(<LoginPage />, { wrapper })
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows error on empty submit', async () => {
    render(<LoginPage />, { wrapper })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
    })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend/apps/web && pnpm test
```

Expected: FAIL — `Cannot find module '../src/app/(auth)/login/page'`

- [ ] **Step 3: Create login page**

```tsx
// frontend/apps/web/src/app/(auth)/login/page.tsx
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'

const LoginSchema = z.object({
  email: z.string().email('Invalid email address').min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormData = z.infer<typeof LoginSchema>

export default function LoginPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: zodResolver(LoginSchema) })

  const onSubmit = async (data: LoginFormData) => {
    setError(null)
    setLoading(true)
    try {
      await apiClient.login(data.email, data.password)
      await queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      router.push('/dashboard')
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-3xl font-display text-text-primary">
            Wine Fermentation System
          </CardTitle>
          <CardDescription>Sign in to your account to continue</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@winery.com"
                {...register('email')}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && (
                <p id="email-error" className="text-sm text-danger">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                {...register('password')}
                aria-describedby={errors.password ? 'password-error' : undefined}
              />
              {errors.password && (
                <p id="password-error" className="text-sm text-danger">{errors.password.message}</p>
              )}
            </div>

            {error && (
              <p className="text-sm text-danger bg-red-50 p-3 rounded">{error}</p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 4: Create root redirect page and 403 page**

```tsx
// frontend/apps/web/src/app/page.tsx
import { redirect } from 'next/navigation'
export default function RootPage() {
  redirect('/dashboard')
}
```

```tsx
// frontend/apps/web/src/app/403/page.tsx
'use client'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background gap-4">
      <h1 className="text-4xl font-display text-text-primary">Access Denied</h1>
      <p className="text-muted text-lg">You don't have permission to view this page.</p>
      <Button asChild variant="outline">
        <Link href="/dashboard">Return to Dashboard</Link>
      </Button>
    </div>
  )
}
```

- [ ] **Step 5: Run tests**

```bash
cd frontend/apps/web && pnpm test
```

Expected: PASS — all tests pass (3 login tests + 1 infrastructure test + 3 auth store tests)

- [ ] **Step 6: Commit**

```bash
git add frontend/apps/web/src/app/
git commit -m "feat: add login page with form validation and 403 access denied page"
```

---

## Task 13: apps/web — Dashboard layout with sidebar + role guard

**Files:**
- Create: `frontend/apps/web/src/components/layout/sidebar.tsx`
- Create: `frontend/apps/web/src/components/layout/topbar.tsx`
- Create: `frontend/apps/web/src/components/layout/admin-layout.tsx`
- Create: `frontend/apps/web/src/app/(dashboard)/layout.tsx`
- Create: `frontend/apps/web/src/app/(dashboard)/dashboard/page.tsx`
- Create: `frontend/apps/web/__tests__/admin-layout.test.tsx`

- [ ] **Step 1: Write failing test for role guard**

```tsx
// frontend/apps/web/__tests__/admin-layout.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock useAuthStore
vi.mock('../src/stores/auth.store', () => ({
  useAuthStore: vi.fn((selector: (s: { user: unknown }) => unknown) =>
    selector({ user: { id: 1, email: 'a@b.com', role: 'WINEMAKER', winery_id: 'w-1' } })
  ),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/dashboard',
}))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
)

describe('AdminLayout', () => {
  it('renders children for authenticated user', async () => {
    const { AdminLayout } = await import('../src/components/layout/admin-layout')
    render(<AdminLayout><div data-testid="content">Content</div></AdminLayout>, { wrapper })
    expect(screen.getByTestId('content')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend/apps/web && pnpm test
```

Expected: FAIL — `Cannot find module '../src/components/layout/admin-layout'`

- [ ] **Step 3: Create sidebar.tsx**

```tsx
// frontend/apps/web/src/components/layout/sidebar.tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth.store'
import {
  LayoutDashboard,
  FlaskConical,
  Bell,
  Zap,
  BookOpen,
  Leaf,
  Building2,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/fermentations', label: 'Fermentations', icon: FlaskConical },
  { href: '/protocols', label: 'Protocols', icon: BookOpen },
  { href: '/fruit-origin', label: 'Fruit Origin', icon: Leaf },
]

const adminItems = [
  { href: '/admin/wineries', label: 'Wineries', icon: Building2 },
]

export function Sidebar() {
  const pathname = usePathname()
  const user = useAuthStore(state => state.user)
  const isAdmin = user?.role === 'ADMIN'

  return (
    <aside className="w-64 min-h-screen bg-surface border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-display font-semibold text-text-primary">
          Fermentation System
        </h1>
        {user && (
          <p className="text-xs text-muted mt-1">{user.email}</p>
        )}
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-sans transition-colors',
              pathname.startsWith(href)
                ? 'bg-accent text-white'
                : 'text-text-primary hover:bg-secondary'
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}

        {isAdmin && (
          <>
            <div className="pt-4 pb-1 px-3">
              <p className="text-xs font-medium text-muted uppercase tracking-wider">Admin</p>
            </div>
            {adminItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-sans transition-colors',
                  pathname.startsWith(href)
                    ? 'bg-accent text-white'
                    : 'text-text-primary hover:bg-secondary'
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </>
        )}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 4: Create topbar.tsx**

```tsx
// frontend/apps/web/src/components/layout/topbar.tsx
'use client'

import { useAuthStore } from '@/stores/auth.store'
import { useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { LogOut } from 'lucide-react'

export function Topbar() {
  const user = useAuthStore(state => state.user)
  const setUser = useAuthStore(state => state.setUser)
  const queryClient = useQueryClient()
  const router = useRouter()

  const handleLogout = async () => {
    await apiClient.logout()
    setUser(null)
    queryClient.clear()
    router.push('/login')
  }

  return (
    <header className="h-14 border-b border-border bg-surface flex items-center justify-end px-6 gap-4">
      {user && (
        <span className="text-sm text-muted">{user.email}</span>
      )}
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        <LogOut size={14} className="mr-1" />
        Logout
      </Button>
    </header>
  )
}
```

- [ ] **Step 5: Create admin-layout.tsx**

```tsx
// frontend/apps/web/src/components/layout/admin-layout.tsx
'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth.store'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = useAuthStore(state => state.user)
  const pathname = usePathname()
  const router = useRouter()

  // Role guard: WINEMAKER cannot access /admin/* routes
  useEffect(() => {
    if (user && user.role === 'WINEMAKER' && pathname.startsWith('/admin')) {
      router.replace('/403')
    }
  }, [user, pathname, router])

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Topbar />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create dashboard layout.tsx**

```tsx
// frontend/apps/web/src/app/(dashboard)/layout.tsx
import { AuthProvider } from '@/providers/auth-provider'
import { AdminLayout } from '@/components/layout/admin-layout'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AdminLayout>{children}</AdminLayout>
    </AuthProvider>
  )
}
```

- [ ] **Step 7: Create dashboard/page.tsx placeholder**

```tsx
// frontend/apps/web/src/app/(dashboard)/dashboard/page.tsx
'use client'

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-display font-semibold text-text-primary mb-6">Dashboard</h1>
      <p className="text-muted">Dashboard content coming in Phase 3.</p>
    </div>
  )
}
```

- [ ] **Step 8: Run all tests**

```bash
cd frontend/apps/web && pnpm test
```

Expected: PASS — all tests pass

- [ ] **Step 9: Type check the whole workspace**

```bash
cd frontend && pnpm type-check
```

Expected: zero TypeScript errors across packages/ui, packages/shared, apps/web

- [ ] **Step 10: Commit**

```bash
git add frontend/apps/web/src/components/layout/ frontend/apps/web/src/app/(dashboard)/
git commit -m "feat: add dashboard layout with sidebar, topbar, and role guard"
```

---

## Task 14: vitest.config files + create .env.local

**Files:**
- Create: `frontend/apps/web/vitest.config.ts`
- Create: `frontend/packages/ui/vitest.config.ts`
- Create: `frontend/packages/shared/vitest.config.ts`
- Create: `frontend/apps/web/.env.local`

- [ ] **Step 1: Create vitest configs**

```typescript
// frontend/apps/web/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./__tests__/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@wine/shared': path.resolve(__dirname, '../../packages/shared/src/index.ts'),
      '@wine/ui': path.resolve(__dirname, '../../packages/ui/src/index.ts'),
    },
  },
})
```

```typescript
// frontend/packages/ui/vitest.config.ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: { environment: 'node', globals: true },
})
```

```typescript
// frontend/packages/shared/vitest.config.ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

- [ ] **Step 2: Create .env.local for web**

```
# frontend/apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:3000
```

- [ ] **Step 3: Run full workspace tests**

```bash
cd frontend && pnpm turbo test
```

Expected: PASS — all tests across packages/ui, packages/shared, apps/web pass

- [ ] **Step 4: Commit**

```bash
git add frontend/apps/web/vitest.config.ts frontend/packages/ui/vitest.config.ts frontend/packages/shared/vitest.config.ts frontend/apps/web/.env.local
git commit -m "chore: add vitest configs for all packages and web app env"
```

---

## Task 15: Final integration check

- [ ] **Step 1: Run full build**

```bash
cd frontend && pnpm turbo build
```

Expected: zero TypeScript errors across all packages; `.next/` folder created in `apps/web`

- [ ] **Step 2: Run full test suite**

```bash
cd frontend && pnpm turbo test
```

Expected: all tests pass across packages/ui, packages/shared, apps/web

- [ ] **Step 3: Start dev server and verify login page loads**

```bash
cd frontend/apps/web && pnpm dev
# Open http://localhost:3000/login in browser
# Should see: "Wine Fermentation System" heading, email field, password field, Sign in button
```

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete frontend foundation — packages/ui, packages/shared, apps/web scaffold with auth"
```

---

## Verification

- [ ] `pnpm turbo test` — all tests pass (zero failures)
- [ ] `pnpm turbo type-check` — zero TypeScript errors
- [ ] `/login` renders correctly: title, email field, password field, sign in button
- [ ] Empty form submit shows "Email is required" validation error
- [ ] `packages/ui` exports: Zod schemas, formatters, constants (all accessible)
- [ ] `packages/shared` exports: ApiClient, TokenStorage, all API functions, all hooks
- [ ] Role guard: WINEMAKER on `/admin/wineries` → redirected to `/403`
- [ ] Dev proxy: `next.config.ts` has rewrites for all 4 backend services
