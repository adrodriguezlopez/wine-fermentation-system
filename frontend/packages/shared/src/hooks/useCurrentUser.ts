import { useQuery } from '@tanstack/react-query'
import Cookies from 'js-cookie'
import type { UserDto } from '../types/auth'
import type { ApiClient } from '../api/client'

export function makeUseCurrentUser(client: ApiClient) {
  return function useCurrentUser() {
    const hasSession = Boolean(
      Cookies.get('wine_access_token') || Cookies.get('wine_refresh_token')
    )

    return useQuery<UserDto>({
      queryKey: ['currentUser'],
      queryFn: () => client.getCurrentUser(),
      staleTime: 5 * 60 * 1000,
      enabled: hasSession,
    })
  }
}
