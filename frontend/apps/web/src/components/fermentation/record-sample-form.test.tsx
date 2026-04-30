import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/utils'
import { RecordSampleForm } from './record-sample-form'

it('renders type selector with 4 options', async () => {
  renderWithProviders(<RecordSampleForm fermentationId={1} />)
  expect(screen.getByLabelText(/density/i)).toBeInTheDocument() // label includes unit
})

it('value field is required', async () => {
  const user = userEvent.setup()
  renderWithProviders(<RecordSampleForm fermentationId={1} />)
  await user.click(screen.getByRole('button', { name: /record sample/i }))
  // zod validation fires — value is required
  await screen.findByText(/required/i)
})
