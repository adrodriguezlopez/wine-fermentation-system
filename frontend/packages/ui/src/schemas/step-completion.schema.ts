import { z } from 'zod'

/**
 * Matches backend CompletionCreateRequest (fermentation/protocol_requests.py).
 *
 * Required: step_id
 * Conditionally required:
 *   - completed_at when was_skipped=false
 *   - skip_reason when was_skipped=true
 */
export const StepCompletionSchema = z
  .object({
    step_id: z.number().int().positive('Step is required'),
    was_skipped: z.boolean().default(false),
    completed_at: z.string().datetime({ offset: true }).optional(),
    is_on_schedule: z.boolean().default(true),
    days_late: z.number().int().min(0).default(0),
    skip_reason: z
      .enum([
        'EQUIPMENT_MALFUNCTION',
        'WEATHER_CONDITIONS',
        'QUALITY_ISSUE',
        'RESOURCE_UNAVAILABLE',
        'OTHER',
      ])
      .optional(),
    skip_notes: z.string().max(500).optional(),
    notes: z.string().max(500).optional(),
  })
  .superRefine((data, ctx) => {
    if (!data.was_skipped && !data.completed_at) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'completed_at is required when not skipping',
        path: ['completed_at'],
      })
    }
    if (data.was_skipped && !data.skip_reason) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'skip_reason is required when skipping',
        path: ['skip_reason'],
      })
    }
  })

export type StepCompletionFormData = z.infer<typeof StepCompletionSchema>
