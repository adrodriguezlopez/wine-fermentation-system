import { useQuery } from '@tanstack/react-query'
import type { UserDto } from '../types/auth'
import type { ApiClient } from '../api/client'

export function makeUseCurrentUser(client: ApiClient) {
  return function useCurrentUser() {
    return useQuery<UserDto>({
      queryKey: ['currentUser'],
      queryFn: () => client.getCurrentUser(),
      staleTime: 5 * 60 * 1000,
    })
  }
}
