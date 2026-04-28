import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useExecutionAlerts, useAcknowledgeAlert, useDismissAlert } from './use-execution'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useExecutionAlerts', () => {
  it('returns alerts list with 1 item', async () => {
    const { result } = renderHook(() => useExecutionAlerts(1), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(1)
  })
})

describe('useAcknowledgeAlert', () => {
  it('acknowledges an alert and returns 200 response', async () => {
    const { result } = renderHook(() => useAcknowledgeAlert(), { wrapper: createWrapper() })
    await act(async () => {
      result.current.mutate(1)
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.status).toBe('ACKNOWLEDGED')
  })
})

describe('useDismissAlert', () => {
  it('dismisses an alert and returns 200 response', async () => {
    const { result } = renderHook(() => useDismissAlert(), { wrapper: createWrapper() })
    await act(async () => {
      result.current.mutate(1)
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.status).toBe('DISMISSED')
  })
})
