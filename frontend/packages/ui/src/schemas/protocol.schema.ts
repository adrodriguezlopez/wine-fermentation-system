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
