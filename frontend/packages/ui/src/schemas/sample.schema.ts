import { z } from 'zod'
import { SAMPLE_TYPES } from '../constants/sample-types'

export const SampleSchema = z.object({
  sample_type: z.enum(SAMPLE_TYPES),
  value: z.number({ required_error: 'Value is required' }),
  units: z.string().min(1).max(20),
  recorded_at: z.string().datetime({ message: 'Must be ISO datetime string' }),
})

export type SampleFormData = z.infer<typeof SampleSchema>
