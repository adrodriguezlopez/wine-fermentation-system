import { useQueryClient, type QueryKey } from '@tanstack/react-query'

const STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000 // 4 hours

export function useStaleDataWarning(queryKey: QueryKey) {
  const queryClient = useQueryClient()
  const state = queryClient.getQueryState(queryKey as string[])

  if (!state?.dataUpdatedAt) {
    return { isStale: false, staleSinceMinutes: 0 }
  }

  const ageMins = (Date.now() - state.dataUpdatedAt) / 60_000
  const isStale = Date.now() - state.dataUpdatedAt > STALE_THRESHOLD_MS

  return { isStale, staleSinceMinutes: Math.round(ageMins) }
}
