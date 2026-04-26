import { useQuery, type QueryKey } from '@tanstack/react-query'

interface UsePollingOptions {
  intervalMs?: number
  enabled?: boolean
}

export function usePolling<T>(
  queryKey: QueryKey,
  queryFn: () => Promise<T>,
  options: UsePollingOptions = {}
) {
  const { intervalMs = 30_000, enabled = true } = options

  return useQuery<T>({
    queryKey,
    queryFn,
    refetchInterval: enabled ? intervalMs : false,
    refetchIntervalInBackground: false,
    enabled,
  })
}
