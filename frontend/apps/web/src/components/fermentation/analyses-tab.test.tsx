import { describe, it, expect, beforeAll, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '@/test/utils'
import { server } from '@/test/setup'
import { AnalysesTab } from './analyses-tab'

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
})

describe('AnalysesTab', () => {
  it('renders list of analyses from MSW', async () => {
    renderWithProviders(<AnalysesTab fermentationId={1} />)

    await waitFor(() => {
      expect(screen.getByText(/2024/)).toBeInTheDocument()
    })
    expect(screen.getByText('1 anomaly')).toBeInTheDocument()
    expect(screen.getByText('2 recommendations')).toBeInTheDocument()
  })

  it("'Run Analysis' button calls POST /analyses via MSW", async () => {
    let posted = false
    server.use(
      http.post('/api/analysis/api/v1/analyses', async () => {
        posted = true
        return HttpResponse.json({ id: 'analysis-new', fermentation_id: '1' }, { status: 201 })
      })
    )

    renderWithProviders(<AnalysesTab fermentationId={1} />)

    const button = screen.getByRole('button', { name: /run analysis/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(posted).toBe(true)
    })
  })

  it('button is disabled while mutation in flight', async () => {
    server.use(
      http.post('/api/analysis/api/v1/analyses', async () => {
        await new Promise((resolve) => setTimeout(resolve, 500))
        return HttpResponse.json({ id: 'analysis-new', fermentation_id: '1' }, { status: 201 })
      })
    )

    renderWithProviders(<AnalysesTab fermentationId={1} />)

    const button = screen.getByRole('button', { name: /run analysis/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /run analysis/i })).toBeDisabled()
    })
  })

  it('shows empty state when no analyses', async () => {
    server.use(
      http.get('/api/analysis/api/v1/analyses/fermentation/:id', () => {
        return HttpResponse.json([])
      })
    )

    renderWithProviders(<AnalysesTab fermentationId={1} />)

    await waitFor(() => {
      expect(
        screen.getByText(/no analyses yet — run one to detect anomalies/i)
      ).toBeInTheDocument()
    })
  })
})
