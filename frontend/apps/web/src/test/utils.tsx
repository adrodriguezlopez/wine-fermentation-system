import React from 'react'
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach } from 'vitest'

const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchInterval: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
})

beforeEach(() => {
  testQueryClient.clear()
})

export function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  )
}
