import { z } from 'zod'

const currentYear = new Date().getFullYear()

export const CreateFermentationSchema = z.object({
  vintage_year: z.number().int().min(1900).max(currentYear + 1),
  yeast_strain: z.string().min(1, 'Yeast strain is required'),
  vessel_code: z.string().min(1, 'Vessel code is required'),
  input_mass_kg: z.number().positive('Input mass must be positive'),
  initial_sugar_brix: z.number().min(0).max(50),
  initial_density: z.number().optional(),
  start_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
  notes: z.string().max(1000).optional(),
})

export const BlendFermentationSchema = CreateFermentationSchema.extend({
  lot_sources: z
    .array(
      z.object({
        harvest_lot_id: z.string().uuid(),
        percentage: z.number().min(0).max(100),
      })
    )
    .min(2, 'Blend must have at least 2 sources'),
})

export const UpdateFermentationSchema = CreateFermentationSchema.partial()

export type CreateFermentationData = z.infer<typeof CreateFermentationSchema>
export type BlendFermentationData = z.infer<typeof BlendFermentationSchema>
export type UpdateFermentationData = z.infer<typeof UpdateFermentationSchema>
