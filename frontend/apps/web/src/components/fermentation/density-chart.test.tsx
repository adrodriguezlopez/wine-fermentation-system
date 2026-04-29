import { vi } from 'vitest'

vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { render, screen } from '@testing-library/react'
import { DensityChart } from './density-chart'
import type { SampleDto } from '@wine/shared'

const makeSample = (id: number, type: string, value: number, date: string): SampleDto => ({
  id, fermentation_id: 1, sample_type: type as 'density', value,
  units: 'g/cm³', recorded_at: date, created_at: date, updated_at: date,
})

it('renders chart when 2+ density samples exist', () => {
  const samples = [
    makeSample(1, 'density', 1.095, '2024-06-01T10:00:00Z'),
    makeSample(2, 'density', 1.080, '2024-06-02T10:00:00Z'),
  ]
  render(<DensityChart samples={samples} />)
  expect(screen.getByTestId('line-chart')).toBeInTheDocument()
})

it('shows empty state when fewer than 2 density samples', () => {
  const samples = [makeSample(1, 'density', 1.095, '2024-06-01T10:00:00Z')]
  render(<DensityChart samples={samples} />)
  expect(screen.getByText('Not enough data to display chart')).toBeInTheDocument()
})

it('ignores non-density samples', () => {
  const samples = [
    makeSample(1, 'density', 1.095, '2024-06-01T10:00:00Z'),
    makeSample(2, 'temperature', 22.5, '2024-06-01T11:00:00Z'),
  ]
  render(<DensityChart samples={samples} />)
  // Only 1 density sample → empty state
  expect(screen.getByText('Not enough data to display chart')).toBeInTheDocument()
})
