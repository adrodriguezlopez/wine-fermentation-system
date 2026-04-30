import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/test/utils'
import { ProtocolTab } from './protocol-tab'

it('shows "Assign protocol" button when no execution', () => {
  renderWithProviders(<ProtocolTab fermentationId={1} executionId={undefined} />)
  expect(screen.getByRole('button', { name: /assign a protocol/i })).toBeInTheDocument()
})

it('shows execution detail when execution exists', async () => {
  renderWithProviders(<ProtocolTab fermentationId={1} executionId={1} />)
  await screen.findByText('Protocol Execution')
  expect(screen.getByText(/ACTIVE/i)).toBeInTheDocument()
})

it('shows protocol selector after clicking assign button', async () => {
  renderWithProviders(<ProtocolTab fermentationId={1} executionId={undefined} />)
  fireEvent.click(screen.getByRole('button', { name: /assign a protocol/i }))
  expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
})
