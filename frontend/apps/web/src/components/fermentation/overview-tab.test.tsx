import { vi } from 'vitest'

vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null, XAxis: () => null, YAxis: () => null,
  Tooltip: () => null, CartesianGrid: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import { renderWithProviders } from '@/test/utils'
import { OverviewTab } from './overview-tab'
import type { FermentationDto } from '@wine/shared'

const fermentation: FermentationDto = {
  id: 1, winery_id: 1, vintage_year: 2024, yeast_strain: 'EC-1118',
  vessel_code: 'VAT-01', input_mass_kg: 5000, initial_sugar_brix: 24.5,
  initial_density: 1.102, start_date: '2024-06-01T00:00:00Z',
  status: 'ACTIVE', notes: null, created_at: '2024-06-01T00:00:00Z', updated_at: '2024-06-01T00:00:00Z'
}

it('renders latest sample value', async () => {
  renderWithProviders(<OverviewTab fermentation={fermentation} />)
  // MSW returns density sample with value 1.095
  await screen.findByText(/1\.09[0-9]/i)
})

it('renders statistics section', async () => {
  renderWithProviders(<OverviewTab fermentation={fermentation} />)
  await screen.findByText('Total Samples')
})

it('shows "not enough data" when only 1 density sample', async () => {
  server.use(
    http.get('/api/fermentation/api/v1/fermentations/:id/samples', () =>
      HttpResponse.json([
        { id: 1, fermentation_id: 1, sample_type: 'density', value: 1.095, units: 'g/cm³', recorded_at: '2024-06-01T10:00:00Z', created_at: '2024-06-01T10:00:00Z', updated_at: '2024-06-01T10:00:00Z' }
      ])
    )
  )
  renderWithProviders(<OverviewTab fermentation={fermentation} />)
  await screen.findByText('Not enough data to display chart')
})
