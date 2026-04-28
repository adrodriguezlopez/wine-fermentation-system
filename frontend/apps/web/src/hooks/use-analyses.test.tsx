// MSW handlers are set up globally in src/test/setup.ts
// server.use(...) overrides are available via the exported `server`
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useTriggerAnalysis, useFermentationAnalyses, useAnalysis } from './use-analyses'

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

describe('useFermentationAnalyses', () => {
  it('returns a list with 1 analysis item', async () => {
    const { result } = renderHook(() => useFermentationAnalyses(1), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(1)
  })
})

describe('useAnalysis', () => {
  it('returns a single analysis with an anomalies array', async () => {
    const { result } = renderHook(() => useAnalysis('analysis-1'), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data?.anomalies)).toBe(true)
  })
})
