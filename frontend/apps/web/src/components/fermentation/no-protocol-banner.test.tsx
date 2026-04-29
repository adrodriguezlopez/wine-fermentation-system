import { render, screen } from '@testing-library/react'
import { NoProtocolBanner } from './no-protocol-banner'

it('renders when hasExecution is false', () => {
  render(<NoProtocolBanner hasExecution={false} />)
  expect(screen.getByText(/no protocol assigned/i)).toBeInTheDocument()
})

it('does not render when hasExecution is true', () => {
  render(<NoProtocolBanner hasExecution={true} />)
  expect(screen.queryByText(/no protocol assigned/i)).not.toBeInTheDocument()
})
