import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { AlertRow } from './alert-row'
import type { AlertDto } from '@wine/shared'

const alert: AlertDto = {
  id: 1, execution_id: 1, protocol_id: 1, winery_id: 1,
  step_id: null, step_name: null,
  alert_type: 'TEMPERATURE_HIGH', severity: 'WARNING',
  status: 'PENDING', message: 'Temperature is too high',
  created_at: '2024-06-01T10:00:00Z', sent_at: null,
  acknowledged_at: null, dismissed_at: null
}

it('renders alert message and severity badge', () => {
  render(<AlertRow alert={alert} onAcknowledge={vi.fn()} onDismiss={vi.fn()} />)
  expect(screen.getByText('Temperature is too high')).toBeInTheDocument()
  expect(screen.getByText('WARNING')).toBeInTheDocument()
})

it('renders both Acknowledge AND Dismiss buttons', () => {
  render(<AlertRow alert={alert} onAcknowledge={vi.fn()} onDismiss={vi.fn()} />)
  expect(screen.getByRole('button', { name: /acknowledge/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
})

it('calls onAcknowledge with correct id', () => {
  const onAck = vi.fn()
  render(<AlertRow alert={alert} onAcknowledge={onAck} onDismiss={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: /acknowledge/i }))
  expect(onAck).toHaveBeenCalledWith(1)
})

it('calls onDismiss with correct id', () => {
  const onDismiss = vi.fn()
  render(<AlertRow alert={alert} onAcknowledge={vi.fn()} onDismiss={onDismiss} />)
  fireEvent.click(screen.getByRole('button', { name: /dismiss/i }))
  expect(onDismiss).toHaveBeenCalledWith(1)
})

it('shows muted icon when alert is acknowledged', () => {
  const acknowledgedAlert = { ...alert, acknowledged_at: '2024-06-01T11:00:00Z' }
  render(<AlertRow alert={acknowledgedAlert} onAcknowledge={vi.fn()} onDismiss={vi.fn()} />)
  expect(screen.getByLabelText('acknowledged')).toBeInTheDocument()
})
