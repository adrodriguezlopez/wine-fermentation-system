// MSW handlers are set up globally in src/test/setup.ts
// server.use(...) overrides are available via the exported `server`
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useExecutionAlerts, useAcknowledgeAlert, useDismissAlert, useAssignProtocol } from './use-execution'

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

describe('useAssignProtocol', () => {
  it('mutates with fermentationId and protocolId and response has fermentation_id', async () => {
    const { result } = renderHook(() => useAssignProtocol(), { wrapper: createWrapper() })
    await act(async () => {
      result.current.mutate({ fermentationId: 1, protocolId: 1 })
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.fermentation_id).toBeDefined()
  })
})
