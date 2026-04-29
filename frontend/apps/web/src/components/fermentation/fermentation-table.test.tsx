import { render, screen } from '@testing-library/react'
import { FermentationTable } from './fermentation-table'
import type { FermentationDto } from '@wine/shared'

const mockFermentations: FermentationDto[] = [
  {
    id: 1, winery_id: 1, vintage_year: 2024, yeast_strain: 'EC-1118',
    vessel_code: 'VAT-01', input_mass_kg: 5000, initial_sugar_brix: 24.5,
    initial_density: 1.102, start_date: '2024-06-01T00:00:00Z',
    status: 'ACTIVE', notes: null, created_at: '2024-06-01T00:00:00Z', updated_at: '2024-06-01T00:00:00Z'
  },
  {
    id: 2, winery_id: 1, vintage_year: 2022, yeast_strain: 'RC-212',
    vessel_code: 'VAT-02', input_mass_kg: 3000, initial_sugar_brix: 22.0,
    initial_density: 1.092, start_date: '2024-06-10T00:00:00Z',
    status: 'ACTIVE', notes: null, created_at: '2024-06-10T00:00:00Z', updated_at: '2024-06-10T00:00:00Z'
  }
]

it('renders 2 rows from data', () => {
  render(<FermentationTable fermentations={mockFermentations} isLoading={false} />)
  expect(screen.getByText('VAT-01')).toBeInTheDocument()
  expect(screen.getByText('VAT-02')).toBeInTheDocument()
})

it('renders status badges', () => {
  render(<FermentationTable fermentations={mockFermentations} isLoading={false} />)
  const badges = screen.getAllByText('ACTIVE')
  expect(badges.length).toBe(2)
})

it('shows loading skeleton when isLoading=true', () => {
  const { container } = render(<FermentationTable fermentations={[]} isLoading={true} />)
  expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
})

it('shows empty state when list is empty', () => {
  render(<FermentationTable fermentations={[]} isLoading={false} />)
  expect(screen.getByText('No fermentations found')).toBeInTheDocument()
})
