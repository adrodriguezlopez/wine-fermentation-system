import { z } from 'zod'

export const STEP_TYPES = [
  'INITIALIZATION',
  'MONITORING',
  'ADDITIONS',
  'CAP_MANAGEMENT',
  'POST_FERMENTATION',
  'QUALITY_CHECK',
] as const

export const ProtocolSchema = z.object({
  varietal_code: z.string().min(1, 'Varietal code is required').max(4),
  varietal_name: z.string().min(1, 'Varietal name is required').max(100),
  color: z.enum(['RED', 'WHITE', 'ROSÉ']),
  protocol_name: z.string().min(1, 'Protocol name is required').max(255),
  version: z.string().regex(/^\d+\.\d+$/, 'Must be X.Y format e.g. 1.0'),
  expected_duration_days: z.number().int().positive(),
  description: z.string().max(2000).optional(),
})

export const ProtocolStepSchema = z.object({
  step_type: z.enum(STEP_TYPES),
  step_order: z.number().int().positive(),
  description: z.string().min(1).max(500),
  expected_day: z.number().int().min(0),
  tolerance_hours: z.number().int().min(0),
  duration_minutes: z.number().int().positive(),
  criticality_score: z.number().min(0).max(100),
  can_repeat_daily: z.boolean().default(false),
  depends_on_step_id: z.number().int().positive().optional(),
  notes: z.string().max(500).optional(),
})

export type ProtocolFormData = z.infer<typeof ProtocolSchema>
export type ProtocolStepFormData = z.infer<typeof ProtocolStepSchema>
