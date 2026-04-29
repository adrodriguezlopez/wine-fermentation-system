import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import { renderWithProviders } from '@/test/utils'
import { AlertsTab } from './alerts-tab'

it('shows alerts list when execution is active', async () => {
  renderWithProviders(<AlertsTab executionId={1} executionStatus="ACTIVE" />)
  await screen.findByText('Temperature is above recommended range') // from MSW fixture
})

it('shows "Protocol completed" banner when execution completed', async () => {
  server.use(
    http.get('/api/fermentation/executions/:id/alerts', () =>
      HttpResponse.json({ items: [], total: 0, pending_count: 0 })
    )
  )
  renderWithProviders(<AlertsTab executionId={1} executionStatus="COMPLETED" />)
  await screen.findByText(/protocol completed/i)
})

it('shows "No protocol" message when no executionId', () => {
  renderWithProviders(<AlertsTab executionId={undefined} />)
  expect(screen.getByText(/no protocol assigned/i)).toBeInTheDocument()
})
