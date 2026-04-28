import { describe, it, expect } from 'vitest'

describe('MSW fermentation handlers', () => {
  it('GET /api/fermentation/fermentations returns paginated response with 2 items', async () => {
    const res = await fetch('/api/fermentation/fermentations')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.items).toHaveLength(2)
    expect(data.total).toBe(2)
    expect(data.items[0].status).toBe('ACTIVE')
    expect(data.items[1].status).toBe('ACTIVE')
  })

  it('GET /api/fermentation/fermentations/:id returns single fermentation with correct shape', async () => {
    const res = await fetch('/api/fermentation/fermentations/1')
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
})
