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
