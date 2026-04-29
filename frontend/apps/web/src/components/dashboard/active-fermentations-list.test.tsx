import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '@/test/utils'
import { server } from '@/test/setup'
import { ActiveFermentationsList } from './active-fermentations-list'

describe('ActiveFermentationsList', () => {
  it('renders fermentations from MSW handler', async () => {
    renderWithProviders(<ActiveFermentationsList />)
    await waitFor(() => {
      expect(screen.getByText('VAT-01')).toBeInTheDocument()
      expect(screen.getByText('VAT-02')).toBeInTheDocument()
    })
  })

  it('shows "No active fermentations" when handler returns empty list', async () => {
    server.use(
      http.get('/api/fermentation/fermentations', () => {
        return HttpResponse.json({ items: [], total: 0, page: 1, size: 20 })
      })
    )
    renderWithProviders(<ActiveFermentationsList />)
    await waitFor(() => {
      expect(screen.getByText('No active fermentations')).toBeInTheDocument()
    })
  })
})
