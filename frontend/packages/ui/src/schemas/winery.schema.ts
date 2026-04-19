import { z } from 'zod'

export const WinerySchema = z.object({
  name: z.string().min(1, 'Winery name is required'),
  code: z.string().min(2).max(10).transform(s => s.toUpperCase()),
  location: z.string().optional(),
})

export type WineryFormData = z.infer<typeof WinerySchema>
