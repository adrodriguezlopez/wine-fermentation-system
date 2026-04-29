import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { FermentationTabs } from './fermentation-tabs'

it('renders all 5 tabs', () => {
  render(<FermentationTabs activeTab="overview" onTabChange={vi.fn()} hasExecution={true} alertCount={0} />)
  expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: /samples/i })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: /alerts/i })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: /protocol/i })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: /actions/i })).toBeInTheDocument()
})

it('active tab has aria-selected=true', () => {
  render(<FermentationTabs activeTab="samples" onTabChange={vi.fn()} hasExecution={true} alertCount={0} />)
  expect(screen.getByRole('tab', { name: /samples/i })).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByRole('tab', { name: /overview/i })).toHaveAttribute('aria-selected', 'false')
})

it('shows alert badge when alertCount > 0 and hasExecution', () => {
  render(<FermentationTabs activeTab="overview" onTabChange={vi.fn()} hasExecution={true} alertCount={3} />)
  expect(screen.getByText('3')).toBeInTheDocument()
})

it('hides alert badge when alertCount === 0', () => {
  render(<FermentationTabs activeTab="overview" onTabChange={vi.fn()} hasExecution={true} alertCount={0} />)
  expect(screen.queryByText('0')).not.toBeInTheDocument()
})

it('calls onTabChange when a tab is clicked', () => {
  const onTabChange = vi.fn()
  render(<FermentationTabs activeTab="overview" onTabChange={onTabChange} hasExecution={true} alertCount={0} />)
  fireEvent.click(screen.getByRole('tab', { name: /samples/i }))
  expect(onTabChange).toHaveBeenCalledWith('samples')
})
