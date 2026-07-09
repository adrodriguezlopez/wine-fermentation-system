'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Cookies from 'js-cookie'
import { makeUseCurrentUser } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'

const useCurrentUser = makeUseCurrentUser(apiClient)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const setUser = useAuthStore((s) => s.setUser)
  const clearUser = useAuthStore((s) => s.clearUser)
  const hasSession = Boolean(
    Cookies.get('wine_access_token') || Cookies.get('wine_refresh_token')
  )

  const { data: user, isError } = useCurrentUser()

  useEffect(() => {
    if (user) {
      setUser(user)
    }
  }, [user, setUser])

  useEffect(() => {
    if (!hasSession && !pathname.startsWith('/login')) {
      clearUser()
      router.replace('/login')
      return
    }

    if (isError && hasSession) {
      clearUser()
      if (!pathname.startsWith('/login')) {
        router.replace('/login')
      }
    }
  }, [hasSession, isError, clearUser, router, pathname])

  return <>{children}</>
}
