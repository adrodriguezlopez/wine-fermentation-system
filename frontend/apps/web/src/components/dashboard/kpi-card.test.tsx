import { render, screen } from '@testing-library/react'
import { Activity } from 'lucide-react'
import { KpiCard } from './kpi-card'

describe('KpiCard', () => {
  it('renders label and value', () => {
    render(<KpiCard label="Active Fermentations" value={5} icon={Activity} />)
    expect(screen.getByText('Active Fermentations')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders icon', () => {
    const { container } = render(<KpiCard label="Test" value={1} icon={Activity} />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders trend up indicator', () => {
    render(<KpiCard label="Test" value={1} icon={Activity} trend="up" />)
    expect(screen.getByText('↑')).toBeInTheDocument()
  })

  it('renders trend down indicator', () => {
    render(<KpiCard label="Test" value={1} icon={Activity} trend="down" />)
    expect(screen.getByText('↓')).toBeInTheDocument()
  })

  it('renders no trend when not provided', () => {
    render(<KpiCard label="Test" value={1} icon={Activity} />)
    expect(screen.queryByText('↑')).not.toBeInTheDocument()
    expect(screen.queryByText('↓')).not.toBeInTheDocument()
  })
})
