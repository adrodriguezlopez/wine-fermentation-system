import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { ApiClient } from '../api/client'

export function makeUseAuth(client: ApiClient) {
  return function useAuth() {
    const queryClient = useQueryClient()

    const login = useCallback(async (username: string, password: string) => {
      await client.login(username, password)
      await queryClient.invalidateQueries({ queryKey: ['currentUser'] })
    }, [queryClient])

    const logout = useCallback(async () => {
      await client.logout()
      queryClient.clear()
    }, [queryClient])

    return { login, logout }
  }
}
