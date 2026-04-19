import { z } from 'zod'

export const WinerySchema = z.object({
  name: z.string().min(1, 'Winery name is required').max(255),
  code: z.string().min(1).max(100).transform(s => s.toUpperCase()),
  location: z.string().max(500).optional(),
  notes: z.string().optional(),
})

export type WineryFormData = z.infer<typeof WinerySchema>
