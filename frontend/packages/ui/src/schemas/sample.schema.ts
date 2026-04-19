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
