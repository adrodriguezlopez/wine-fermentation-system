import { z } from 'zod'

export const ACTION_TYPES = [
  'TEMPERATURE_ADJUSTMENT',
  'NUTRIENT_ADDITION',
  'SULFUR_ADDITION',
  'PUMP_OVER',
  'PUNCH_DOWN',
  'RACK',
  'FILTRATION',
  'YEAST_ADDITION',
  'H2S_TREATMENT',
  'STUCK_FERMENTATION_PROTOCOL',
  'PROTOCOL_STEP_COMPLETED_LATE',
  'CUSTOM',
] as const
export type ActionType = typeof ACTION_TYPES[number]

export const ActionSchema = z.object({
  action_type: z.enum(ACTION_TYPES),
  description: z.string().min(1, 'Please describe the action taken').max(2000),
  taken_at: z.string().datetime({ message: 'Must be ISO datetime string' }),
  execution_id: z.number().int().positive().optional(),
  step_id: z.number().int().positive().optional(),
  alert_id: z.number().int().positive().optional(),
  recommendation_id: z.number().int().positive().optional(),
})

export const ACTION_OUTCOMES = ['PENDING', 'RESOLVED', 'NO_EFFECT', 'WORSENED'] as const
export type ActionOutcome = typeof ACTION_OUTCOMES[number]

export const UpdateActionOutcomeSchema = z.object({
  outcome: z.enum(ACTION_OUTCOMES),
  outcome_notes: z.string().max(2000).optional(),
})

export type ActionFormData = z.infer<typeof ActionSchema>
export type UpdateActionOutcomeData = z.infer<typeof UpdateActionOutcomeSchema>
