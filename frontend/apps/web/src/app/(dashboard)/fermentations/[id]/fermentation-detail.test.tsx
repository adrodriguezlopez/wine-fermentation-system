import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/test/utils'
import FermentationDetailPage from './page'

it('renders fermentation vessel code from MSW handler', async () => {
  renderWithProviders(<FermentationDetailPage params={{ id: '1' }} />)
  await screen.findByText('VAT-01')
})

it('renders status badge', async () => {
  renderWithProviders(<FermentationDetailPage params={{ id: '1' }} />)
  await screen.findByText('Active')
})

it('default tab is Overview', async () => {
  renderWithProviders(<FermentationDetailPage params={{ id: '1' }} />)
  await screen.findByRole('tab', { name: /overview/i })
  expect(screen.getByRole('tab', { name: /overview/i })).toHaveAttribute('aria-selected', 'true')
})

it('clicking Samples tab switches content', async () => {
  renderWithProviders(<FermentationDetailPage params={{ id: '1' }} />)
  await screen.findByRole('tab', { name: /samples/i })
  fireEvent.click(screen.getByRole('tab', { name: /samples/i }))
  expect(screen.getByTestId('tab-samples')).toBeInTheDocument()
})
