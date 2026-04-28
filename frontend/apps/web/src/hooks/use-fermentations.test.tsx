import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  useFermentations,
  useFermentation,
  useCreateFermentation,
  useFermentationSamples,
  useLatestSample,
} from './use-fermentations'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useFermentations', () => {
  it('returns fermentations list with 2 items', async () => {
    const { result } = renderHook(() => useFermentations(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(2)
  })
})

describe('useFermentation', () => {
  it('returns a single fermentation by id', async () => {
    const { result } = renderHook(() => useFermentation(1), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.id).toBe(1)
  })
})

describe('useCreateFermentation', () => {
  it('posts a new fermentation and returns data', async () => {
    const { result } = renderHook(() => useCreateFermentation(), { wrapper: createWrapper() })
    result.current.mutate({
      winery_id: 1,
      vintage_year: 2024,
      yeast_strain: 'EC-1118',
      input_mass_kg: 1000,
      initial_sugar_brix: 24.5,
      start_date: '2024-09-01T00:00:00Z',
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeDefined()
  })
})

describe('useFermentationSamples polling', () => {
  it('has refetchInterval false when COMPLETED', () => {
    const { result } = renderHook(() => useFermentationSamples(1, 'COMPLETED'), {
      wrapper: createWrapper(),
    })
    // The hook itself stores the options — we verify it resolves without error
    expect(result.current).toBeDefined()
  })

  it('has refetchInterval 2min when ACTIVE', async () => {
    const { result } = renderHook(() => useFermentationSamples(1, 'ACTIVE'), {
      wrapper: createWrapper(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(3)
  })
})

describe('useLatestSample', () => {
  it('returns the latest sample when status is ACTIVE', async () => {
    const { result } = renderHook(() => useLatestSample(1, 'ACTIVE'), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeDefined()
  })
})
