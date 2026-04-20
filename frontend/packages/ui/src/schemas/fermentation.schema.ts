import { z } from 'zod'
import { FermentationStatusSchema } from '../constants/fermentation-status'

export const CreateFermentationSchema = z.object({
  vintage_year: z.number().int().min(1900).max(2100),
  yeast_strain: z.string().min(1, 'Yeast strain is required').max(100),
  vessel_code: z.string().max(50).optional(),
  input_mass_kg: z.number().positive('Input mass must be positive'),
  initial_sugar_brix: z.number().min(0).max(50),
  initial_density: z.number().positive('Initial density must be positive'),
  start_date: z.string().datetime({ message: 'Must be ISO datetime string' }),
})

const LotSourceSchema = z.object({
  harvest_lot_id: z.number().int().positive(),
  mass_used_kg: z.number().positive(),
  notes: z.string().max(200).optional(),
})

// Blend endpoint (POST /api/v1/fermentations/blends) accepts all base fields
// plus lot_sources — the backend creates the fermentation and lot links atomically.
export const BlendFermentationSchema = CreateFermentationSchema.extend({
  lot_sources: z
    .array(LotSourceSchema)
    .min(1, 'Blend must have at least 1 source'),
})

export const UpdateFermentationSchema = CreateFermentationSchema.partial()

// Response schema — validates API response shape at runtime
export const FermentationResponseSchema = z.object({
  id: z.number().int().positive(),
  vintage_year: z.number().int(),
  yeast_strain: z.string(),
  vessel_code: z.string().nullable(),
  input_mass_kg: z.number(),
  initial_sugar_brix: z.number(),
  initial_density: z.number(),
  start_date: z.string(),
  status: FermentationStatusSchema,
  winery_id: z.number().int().positive(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type CreateFermentationData = z.infer<typeof CreateFermentationSchema>
export type BlendFermentationData = z.infer<typeof BlendFermentationSchema>
export type UpdateFermentationData = z.infer<typeof UpdateFermentationSchema>
export type FermentationResponse = z.infer<typeof FermentationResponseSchema>
