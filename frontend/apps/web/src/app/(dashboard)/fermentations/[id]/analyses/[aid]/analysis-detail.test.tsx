import { describe, it, expect, beforeAll, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '@/test/utils'
import { server } from '@/test/setup'
import AnalysisDetailPage from './page'

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
})

const defaultParams = { id: '1', aid: 'analysis-1' }

describe('AnalysisDetailPage', () => {
  it('renders anomalies section', async () => {
    renderWithProviders(<AnalysisDetailPage params={defaultParams} />)

    await waitFor(() => {
      expect(screen.getByText('Temperature spike detected')).toBeInTheDocument()
    })
    expect(screen.getByText('TEMPERATURE_SPIKE')).toBeInTheDocument()
    expect(screen.getByText('WARNING')).toBeInTheDocument()
  })

  it('renders recommendations', async () => {
    renderWithProviders(<AnalysisDetailPage params={defaultParams} />)

    await waitFor(() => {
      expect(screen.getByText('Reduce fermentation temperature')).toBeInTheDocument()
    })
    expect(screen.getByText('ADJUST_TEMPERATURE')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('Apply button calls PUT /recommendations/:id/apply via MSW', async () => {
    let applied = false
    server.use(
      http.put('/api/analysis/recommendations/:id/apply', ({ params }) => {
        applied = true
        return HttpResponse.json({
          id: String(params.id),
          analysis_id: 'analysis-1',
          recommendation_type: 'ADJUST_TEMPERATURE',
          priority: 'HIGH',
          description: 'Reduce fermentation temperature',
          applied: true,
          applied_at: '2024-06-15T14:30:00.000Z',
        })
      })
    )

    renderWithProviders(<AnalysisDetailPage params={defaultParams} />)

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /apply/i }).length).toBeGreaterThan(0)
    })

    fireEvent.click(screen.getAllByRole('button', { name: /apply/i })[0])

    await waitFor(() => {
      expect(applied).toBe(true)
    })
  })

  it('renders advisories section', async () => {
    renderWithProviders(<AnalysisDetailPage params={defaultParams} />)

    await waitFor(() => {
      expect(screen.getByText('Consider reducing temperature')).toBeInTheDocument()
    })
    expect(screen.getByText('TEMPERATURE')).toBeInTheDocument()
  })

  it('back link points to fermentation detail', async () => {
    renderWithProviders(<AnalysisDetailPage params={defaultParams} />)

    await waitFor(() => {
      expect(screen.getByText('Temperature spike detected')).toBeInTheDocument()
    })

    const backLink = screen.getByRole('link', { name: '' })
    expect(backLink).toHaveAttribute('href', '/fermentations/1')
  })
})
