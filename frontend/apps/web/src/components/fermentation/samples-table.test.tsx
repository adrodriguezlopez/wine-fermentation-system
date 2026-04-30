import { render, screen } from '@testing-library/react'
import { SamplesTable } from './samples-table'
import type { SampleDto } from '@wine/shared'

const samples: SampleDto[] = [
  { id: 1, fermentation_id: 1, sample_type: 'density', value: 1.095, units: 'g/cm³', recorded_at: '2024-06-01T10:00:00Z', created_at: '2024-06-01T10:00:00Z', updated_at: '2024-06-01T10:00:00Z' },
  { id: 2, fermentation_id: 1, sample_type: 'temperature', value: 22.5, units: '°C', recorded_at: '2024-06-01T09:00:00Z', created_at: '2024-06-01T09:00:00Z', updated_at: '2024-06-01T09:00:00Z' },
  { id: 3, fermentation_id: 1, sample_type: 'sugar', value: 20.1, units: '°Bx', recorded_at: '2024-06-01T08:00:00Z', created_at: '2024-06-01T08:00:00Z', updated_at: '2024-06-01T08:00:00Z' },
]

it('renders 3 sample rows using SAMPLE_TYPE_LABEL', () => {
  render(<SamplesTable samples={samples} isLoading={false} />)
  expect(screen.getByText('Density')).toBeInTheDocument()
  expect(screen.getByText('Temperature')).toBeInTheDocument()
  expect(screen.getByText('Sugar')).toBeInTheDocument()
})

it('shows empty state when list is empty', () => {
  render(<SamplesTable samples={[]} isLoading={false} />)
  expect(screen.getByText('No samples recorded yet')).toBeInTheDocument()
})

it('shows skeleton when loading', () => {
  const { container } = render(<SamplesTable samples={[]} isLoading={true} />)
  expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
})
