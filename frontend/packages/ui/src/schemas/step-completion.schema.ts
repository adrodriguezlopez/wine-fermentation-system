import { z } from 'zod'

export const StepCompletionSchema = z.object({
  completion_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
  notes: z.string().max(1000).optional(),
})

export type StepCompletionFormData = z.infer<typeof StepCompletionSchema>
