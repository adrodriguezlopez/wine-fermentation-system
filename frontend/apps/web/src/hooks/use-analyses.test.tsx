import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useTriggerAnalysis } from './use-analyses'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useTriggerAnalysis', () => {
  it('triggers analysis and returns an analysis object', async () => {
    const { result } = renderHook(() => useTriggerAnalysis(), { wrapper: createWrapper() })
    let data: unknown
    await result.current.mutateAsync({ fermentation_id: '1' }).then(r => {
      data = r
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(data).toBeDefined()
    expect((data as Record<string, unknown>).id).toBeDefined()
  })
})
