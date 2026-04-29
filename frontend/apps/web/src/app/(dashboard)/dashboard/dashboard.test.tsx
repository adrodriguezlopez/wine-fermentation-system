import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '@/test/utils'
import DashboardPage from './page'

describe('DashboardPage', () => {
  it('renders 3 KPI cards', async () => {
    renderWithProviders(<DashboardPage />)
    expect(screen.getAllByText('Active Fermentations').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Pending Alerts')).toBeInTheDocument()
    expect(screen.getByText('Completed This Month')).toBeInTheDocument()
  })

  it('renders the active fermentations list', async () => {
    renderWithProviders(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('VAT-01')).toBeInTheDocument()
    })
  })
})
