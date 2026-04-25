import { useQuery, queryOptions } from '@tanstack/react-query'
import type { ApiClient } from '../api/client'

export const currentUserQueryOptions = (client: ApiClient) =>
  queryOptions({
    queryKey: ['currentUser'] as const,
    queryFn: () => client.getCurrentUser(),
    staleTime: 5 * 60 * 1000,
  })

export function makeUseCurrentUser(client: ApiClient) {
  return function useCurrentUser() {
    return useQuery(currentUserQueryOptions(client))
  }
}

