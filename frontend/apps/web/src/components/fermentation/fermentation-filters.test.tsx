import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { FermentationFiltersBar } from './fermentation-filters'

const defaultFilters = { status: '', search: '' }

// Radix UI Select uses scrollIntoView which jsdom doesn't implement
beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
  // Radix needs pointer events
  window.HTMLElement.prototype.hasPointerCapture = vi.fn()
  window.HTMLElement.prototype.releasePointerCapture = vi.fn()
  window.HTMLElement.prototype.setPointerCapture = vi.fn()
})

it('renders status dropdown and search input', () => {
  render(<FermentationFiltersBar filters={defaultFilters} onChange={vi.fn()} />)
  expect(screen.getByRole('combobox')).toBeInTheDocument()
  expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
})

it('calls onChange with updated filter object when status changes', async () => {
  const onChange = vi.fn()
  render(<FermentationFiltersBar filters={defaultFilters} onChange={onChange} />)
  // open select and pick 'ACTIVE'
  fireEvent.click(screen.getByRole('combobox'))
  await screen.findByText('Active')
  fireEvent.click(screen.getByText('Active'))
  expect(onChange).toHaveBeenCalledWith({ status: 'ACTIVE', search: '' })
})
