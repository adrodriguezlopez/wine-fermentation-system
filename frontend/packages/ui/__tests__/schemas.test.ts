import { describe, it, expect } from 'vitest'
import { CreateFermentationSchema } from '../src/schemas/fermentation.schema'

describe('CreateFermentationSchema', () => {
  it('rejects missing vintage_year', () => {
    const result = CreateFermentationSchema.safeParse({
      yeast_strain: 'EC-1118',
      vessel_code: 'V-01',
      input_mass_kg: 5000,
      initial_sugar_brix: 22,
      start_date: '2026-04-01T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })

  it('accepts valid fermentation data', () => {
    const result = CreateFermentationSchema.safeParse({
      vintage_year: 2026,
      yeast_strain: 'EC-1118',
      vessel_code: 'V-01',
      input_mass_kg: 5000,
      initial_sugar_brix: 22,
      start_date: '2026-04-01T00:00:00Z',
    })
    expect(result.success).toBe(true)
  })
})
