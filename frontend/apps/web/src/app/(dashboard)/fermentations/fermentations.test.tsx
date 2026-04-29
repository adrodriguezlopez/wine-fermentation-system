import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/utils'
import FermentationsPage from './page'

it('renders filter controls and table', async () => {
  renderWithProviders(<FermentationsPage />)
  expect(screen.getByRole('combobox')).toBeInTheDocument()
  await screen.findByRole('table')
})

it('renders "New Fermentation" button', () => {
  renderWithProviders(<FermentationsPage />)
  expect(screen.getByRole('link', { name: /new fermentation/i })).toBeInTheDocument()
})
