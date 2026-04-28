import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AdminLayout from './admin-layout'

const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => '/admin/users',
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: (selector: any) =>
    selector({
      user: {
        id: 1,
        email: 'winemaker@test.com',
        role: 'WINEMAKER',
        winery_id: 1,
      },
    }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('AdminLayout', () => {
  it('redirects WINEMAKER user away from /admin/* routes', () => {
    render(
      <AdminLayout>
        <div>admin content</div>
      </AdminLayout>,
      { wrapper }
    )
    expect(mockReplace).toHaveBeenCalledWith('/403')
  })
})
