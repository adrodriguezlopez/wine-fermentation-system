import { describe, it, expect } from 'vitest'

describe('MSW fermentation handlers', () => {
  it('GET /api/fermentation/fermentations returns paginated response with 2 items', async () => {
    const res = await fetch('/api/fermentation/api/v1/fermentations')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.items).toHaveLength(2)
    expect(data.total).toBe(2)
    expect(data.items[0].status).toBe('ACTIVE')
    expect(data.items[1].status).toBe('ACTIVE')
  })

  it('GET /api/fermentation/fermentations/:id returns single fermentation with correct shape', async () => {
    const res = await fetch('/api/fermentation/api/v1/fermentations/1')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.id).toBe(1)
    expect(data).toHaveProperty('winery_id')
    expect(data).toHaveProperty('vintage_year')
    expect(data).toHaveProperty('yeast_strain')
    expect(data).toHaveProperty('status')
    expect(data).toHaveProperty('execution_id')
    expect(data.execution_id).toBe(1)
  })

  it('fermentation fixtures are meaningfully different', async () => {
    const res = await fetch('/api/fermentation/api/v1/fermentations')
    const data = await res.json()
    const [f1, f2] = data.items
    expect(f1.id).not.toBe(f2.id)
    expect(f1.vintage_year).not.toBe(f2.vintage_year)
    expect(f1.yeast_strain).not.toBe(f2.yeast_strain)
    expect(f1.initial_sugar_brix).not.toBe(f2.initial_sugar_brix)
    expect(f1.initial_density).not.toBe(f2.initial_density)
  })

  it('POST /api/fermentation/fermentations returns 201 with fermentation id', async () => {
    const res = await fetch('/api/fermentation/api/v1/fermentations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vessel_code: 'VAT-10', vintage_year: 2023 }),
    })
    expect(res.status).toBe(201)
    const data = await res.json()
    expect(data).toHaveProperty('id')
  })

  it('POST /api/fermentation/fermentations/:id/samples returns 201', async () => {
    const res = await fetch('/api/fermentation/api/v1/fermentations/1/samples', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_type: 'density', value: 1.09, units: 'g/cm3' }),
    })
    expect(res.status).toBe(201)
  })

  it('GET /api/fermentation/executions/:id/alerts returns items with 1 alert and pending_count > 0', async () => {
    const res = await fetch('/api/fermentation/api/v1/executions/1/alerts')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.items).toHaveLength(1)
    expect(data.pending_count).toBeGreaterThan(0)
  })

  it('GET /api/analysis/api/v1/analyses/fermentation/:id returns flat array with 1 analysis', async () => {
    const res = await fetch('/api/analysis/api/v1/analyses/fermentation/1')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
    expect(data).toHaveLength(1)
  })

  it('POST /api/fermentation/alerts/:id/acknowledge returns 200 with acknowledged_at set', async () => {
    const res = await fetch('/api/fermentation/api/v1/alerts/1/acknowledge', { method: 'POST' })
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.acknowledged_at).toBeTruthy()
    expect(data.acknowledged_at).toBe('2024-06-15T14:30:00.000Z')
  })
})
