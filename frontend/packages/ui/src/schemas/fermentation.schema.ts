import { z } from 'zod'

export const CreateFermentationSchema = z.object({
  vintage_year: z.number().int().min(1900).max(2100),
  yeast_strain: z.string().min(1, 'Yeast strain is required').max(100),
  vessel_code: z.string().max(50).optional(),
  input_mass_kg: z.number().positive('Input mass must be positive'),
  initial_sugar_brix: z.number().min(0).max(50),
  initial_density: z.number().positive('Initial density must be positive'),
  start_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
})

export const BlendFermentationSchema = CreateFermentationSchema.extend({
  lot_sources: z
    .array(
      z.object({
        harvest_lot_id: z.number().int().positive(),
        mass_used_kg: z.number().positive(),
        notes: z.string().max(200).optional(),
      })
    )
    .min(1, 'Blend must have at least 1 source'),
})

export const UpdateFermentationSchema = CreateFermentationSchema.partial()

export type CreateFermentationData = z.infer<typeof CreateFermentationSchema>
export type BlendFermentationData = z.infer<typeof BlendFermentationSchema>
export type UpdateFermentationData = z.infer<typeof UpdateFermentationSchema>
