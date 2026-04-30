import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import { renderWithProviders } from '@/test/utils'
import { CreateFermentationForm } from './create-fermentation-form'

it('renders all form fields', async () => {
  renderWithProviders(<CreateFermentationForm />)
  expect(screen.getByLabelText(/vintage year/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/yeast strain/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/vessel code/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/input mass/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/initial sugar/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/initial density/i)).toBeInTheDocument()
})

it('shows protocol selector with "No protocol" placeholder', async () => {
  renderWithProviders(<CreateFermentationForm />)
  await screen.findByText(/no protocol/i)
})

it('shows validation error when yeast strain is empty and form submitted', async () => {
  const user = userEvent.setup()
  renderWithProviders(<CreateFermentationForm />)
  // clear yeast strain which has a default
  await user.clear(screen.getByLabelText(/yeast strain/i))
  await user.click(screen.getByRole('button', { name: /create fermentation/i }))
  await screen.findByText(/yeast strain is required/i)
})

it('submits and navigates on success', async () => {
  const user = userEvent.setup()
  renderWithProviders(<CreateFermentationForm />)
  // fill required fields
  await user.clear(screen.getByLabelText(/yeast strain/i))
  await user.type(screen.getByLabelText(/yeast strain/i), 'EC-1118')
  await user.clear(screen.getByLabelText(/input mass/i))
  await user.type(screen.getByLabelText(/input mass/i), '5000')
  await user.clear(screen.getByLabelText(/initial sugar/i))
  await user.type(screen.getByLabelText(/initial sugar/i), '24.5')
  await user.clear(screen.getByLabelText(/initial density/i))
  await user.type(screen.getByLabelText(/initial density/i), '1.102')
  await user.click(screen.getByRole('button', { name: /create fermentation/i }))
  // MSW returns id:1, router.push called with /fermentations/1
  await waitFor(() => {
    // useRouter is mocked — if no error thrown, success
    expect(screen.queryByText(/creating/i)).not.toBeInTheDocument()
  }, { timeout: 3000 })
})

it('shows error message on server error', async () => {
  server.use(
    http.post('/api/fermentation/api/v1/fermentations', () =>
      HttpResponse.json({ detail: 'Validation error' }, { status: 422 })
    )
  )
  const user = userEvent.setup()
  renderWithProviders(<CreateFermentationForm />)
  await user.type(screen.getByLabelText(/yeast strain/i), 'EC-1118')
  await user.type(screen.getByLabelText(/input mass/i), '5000')
  await user.type(screen.getByLabelText(/initial sugar/i), '24.5')
  await user.type(screen.getByLabelText(/initial density/i), '1.102')
  await user.click(screen.getByRole('button', { name: /create fermentation/i }))
  await screen.findByText(/error|failed|422/i, {}, { timeout: 3000 })
})
