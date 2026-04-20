# Component Context: Schemas (`packages/ui/src/schemas/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Zod validation schemas** for all create and update forms. Used in both web (React Hook Form + Zod resolver) and mobile (manual validation or React Hook Form Native). Defining schemas here guarantees identical validation rules on both platforms.

## Architecture pattern

One schema file per backend resource. Each file exports a Zod schema object and an inferred TypeScript type.

## Files

### `sample.schema.ts`
```typescript
export const SampleSchema = z.object({
  sample_type: z.enum(['DENSITY', 'TEMPERATURE', 'BRIX', 'PH', 'SO2', ...]),
  value: z.number().positive('Value must be positive'),
  recorded_at: z.string().datetime(),
  notes: z.string().max(500).optional(),
})
export type SampleFormData = z.infer<typeof SampleSchema>
```

### `fermentation.schema.ts`
```typescript
export const CreateFermentationSchema = z.object({
  vintage_year: z.number().int().min(1900).max(currentYear),
  yeast_strain: z.string().min(1),
  vessel_code: z.string().min(1),
  input_mass_kg: z.number().positive(),
  initial_sugar_brix: z.number().min(0).max(50),
  initial_density: z.number().optional(),
  start_date: z.string().datetime(),
})
export const BlendFermentationSchema = CreateFermentationSchema.extend({
  lot_sources: z.array(z.object({ harvest_lot_id: z.string().uuid(), percentage: z.number().min(0).max(100) })).min(2),
})
```

### `action.schema.ts`
```typescript
export const ActionSchema = z.object({
  action_type: z.enum(['TEMPERATURE_ADJUSTMENT', 'NUTRIENT_ADDITION', 'PUMP_OVER', ...]),
  description: z.string().min(10, 'Please describe the action taken'),
  taken_at: z.string().datetime(),
  alert_id: z.string().uuid().optional(),
  recommendation_id: z.string().uuid().optional(),
})
```

### `protocol.schema.ts`
```typescript
export const ProtocolSchema = z.object({
  varietal_code: z.string().min(1),
  varietal_name: z.string().min(1),
  version: z.string().regex(/^\d+\.\d+\.\d+$/, 'Must be semver format e.g. 1.0.0'),
  expected_duration_days: z.number().int().positive(),
  description: z.string().optional(),
})
export const ProtocolStepSchema = z.object({
  step_type: z.enum([...]),
  sequence: z.number().int().positive(),
  duration_hours: z.number().positive(),
  threshold_values: z.record(z.number()).optional(),
})
```

### `winery.schema.ts`
```typescript
export const WinerySchema = z.object({
  name: z.string().min(1),
  code: z.string().min(2).max(10).toUpperCase(),
  location: z.string().optional(),
})
```

### `step-completion.schema.ts`
```typescript
export const StepCompletionSchema = z.object({
  completion_date: z.string().datetime(),
  notes: z.string().max(1000).optional(),
})
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 1 / packages/ui
