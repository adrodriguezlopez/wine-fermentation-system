import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { ActionRow } from './action-row'
import type { ActionDto } from '@wine/shared'

const action: ActionDto = {
  id: 1, winery_id: 1, taken_by_user_id: 1, fermentation_id: 1,
  execution_id: null, step_id: null, alert_id: null, recommendation_id: null,
  action_type: 'PUMP_OVER', description: 'Performed pump over',
  taken_at: '2024-06-01T10:00:00Z', outcome: 'PENDING',
  outcome_notes: null, outcome_recorded_at: null,
  created_at: '2024-06-01T10:00:00Z', updated_at: '2024-06-01T10:00:00Z'
}

it('renders action type and description', () => {
  render(<ActionRow action={action} />)
  expect(screen.getByText('Pump Over')).toBeInTheDocument()
  expect(screen.getByText('Performed pump over')).toBeInTheDocument()
})

it('"Update Outcome" button is present', () => {
  render(<ActionRow action={action} />)
  expect(screen.getByRole('button', { name: /update outcome/i })).toBeInTheDocument()
})

it('shows outcome select when Update Outcome clicked', () => {
  render(<ActionRow action={action} />)
  fireEvent.click(screen.getByRole('button', { name: /update outcome/i }))
  expect(screen.getByDisplayValue('Pending')).toBeInTheDocument()
})
