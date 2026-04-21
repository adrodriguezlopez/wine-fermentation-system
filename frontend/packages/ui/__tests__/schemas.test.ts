import { describe, it, expect } from 'vitest'
import { CreateFermentationSchema } from '../src/schemas/fermentation.schema'
import { SampleSchema } from '../src/schemas/sample.schema'
import { ActionSchema, UpdateActionOutcomeSchema } from '../src/schemas/action.schema'

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
      initial_density: 1.095,
      start_date: '2026-04-01T00:00:00Z',
    })
    expect(result.success).toBe(true)
  })
})

describe('SampleSchema', () => {
  const validSample = {
    sample_type: 'temperature' as const,
    value: 18.5,
    units: '°C',
    recorded_at: '2026-04-01T10:00:00Z',
  }

  it('accepts valid sample data', () => {
    expect(SampleSchema.safeParse(validSample).success).toBe(true)
  })

  it('rejects invalid sample_type', () => {
    const result = SampleSchema.safeParse({ ...validSample, sample_type: 'BRIX' })
    expect(result.success).toBe(false)
  })

  it('rejects uppercase sample_type (must use lowercase)', () => {
    const result = SampleSchema.safeParse({ ...validSample, sample_type: 'TEMPERATURE' })
    expect(result.success).toBe(false)
  })

  it('rejects missing value', () => {
    const { value: _, ...rest } = validSample
    const result = SampleSchema.safeParse(rest)
    expect(result.success).toBe(false)
  })

  it('rejects non-datetime recorded_at', () => {
    const result = SampleSchema.safeParse({ ...validSample, recorded_at: '2026-04-01' })
    expect(result.success).toBe(false)
  })

  it('accepts all backend sample types', () => {
    const types = ['sugar', 'temperature', 'density', 'acetic_acid']
    for (const sample_type of types) {
      const result = SampleSchema.safeParse({ ...validSample, sample_type })
      expect(result.success, `Expected ${sample_type} to be valid`).toBe(true)
    }
  })
})

describe('ActionSchema', () => {
  const validAction = {
    action_type: 'PUMP_OVER' as const,
    description: 'Performed pump over to oxygenate must',
    taken_at: '2026-04-01T14:00:00Z',
  }

  it('accepts valid action data', () => {
    expect(ActionSchema.safeParse(validAction).success).toBe(true)
  })

  it('rejects invalid action_type', () => {
    const result = ActionSchema.safeParse({ ...validAction, action_type: 'INVALID' })
    expect(result.success).toBe(false)
  })

  it('rejects empty description', () => {
    const result = ActionSchema.safeParse({ ...validAction, description: '' })
    expect(result.success).toBe(false)
  })

  it('rejects missing description', () => {
    const { description: _, ...rest } = validAction
    const result = ActionSchema.safeParse(rest)
    expect(result.success).toBe(false)
  })

  it('accepts optional FK fields when provided', () => {
    const result = ActionSchema.safeParse({
      ...validAction,
      execution_id: 1,
      step_id: 2,
      alert_id: 3,
      recommendation_id: 4,
    })
    expect(result.success).toBe(true)
  })

  it('rejects non-positive FK ids', () => {
    const result = ActionSchema.safeParse({ ...validAction, execution_id: 0 })
    expect(result.success).toBe(false)
  })
})

describe('UpdateActionOutcomeSchema', () => {
  it('accepts valid outcome', () => {
    expect(UpdateActionOutcomeSchema.safeParse({ outcome: 'RESOLVED' }).success).toBe(true)
  })

  it('rejects invalid outcome', () => {
    expect(UpdateActionOutcomeSchema.safeParse({ outcome: 'UNKNOWN' }).success).toBe(false)
  })

  it('accepts optional outcome_notes', () => {
    const result = UpdateActionOutcomeSchema.safeParse({
      outcome: 'NO_EFFECT',
      outcome_notes: 'Temperature did not change',
    })
    expect(result.success).toBe(true)
  })
})
