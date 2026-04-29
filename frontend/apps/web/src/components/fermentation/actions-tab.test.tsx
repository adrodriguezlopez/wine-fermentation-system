import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/utils'
import { ActionsTab } from './actions-tab'
import type { FermentationDto } from '@wine/shared'

const fermentation: FermentationDto = {
  id: 1, winery_id: 1, vintage_year: 2024, yeast_strain: 'EC-1118',
  vessel_code: 'VAT-01', input_mass_kg: 5000, initial_sugar_brix: 24.5,
  initial_density: 1.102, start_date: '2024-06-01T00:00:00Z',
  status: 'ACTIVE', notes: null, created_at: '2024-06-01T00:00:00Z', updated_at: '2024-06-01T00:00:00Z'
}

it('renders 1 action from MSW handler', async () => {
  renderWithProviders(<ActionsTab fermentation={fermentation} />)
  const elements = await screen.findAllByText('Pump Over')
  // At least the action log entry (could also appear in form select)
  expect(elements.length).toBeGreaterThanOrEqual(1)
})

it('shows empty state when no actions', async () => {
  // override MSW
  const { http, HttpResponse } = await import('msw')
  const { server } = await import('@/test/setup')
  server.use(
    http.get('/api/fermentation/fermentations/:id/actions', () =>
      HttpResponse.json({ items: [], total: 0, skip: 0, limit: 20 })
    )
  )
  renderWithProviders(<ActionsTab fermentation={fermentation} />)
  await screen.findByText('No actions recorded')
})

it('record action form is present', () => {
  renderWithProviders(<ActionsTab fermentation={fermentation} />)
  expect(screen.getByRole('button', { name: /record action/i })).toBeInTheDocument()
})
