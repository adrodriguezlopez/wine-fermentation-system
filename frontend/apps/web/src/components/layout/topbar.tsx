'use client'

import { makeUseAuth } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'

const useAuth = makeUseAuth(apiClient)

export default function Topbar() {
  const { logout } = useAuth()
  const user = useAuthStore((s) => s.user)

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-4">
      <div className="text-sm text-muted-foreground">
        {user?.email}
        {user?.role && (
          <span className="ml-2 rounded bg-accent px-1.5 py-0.5 text-xs font-medium">
            {user.role}
          </span>
        )}
      </div>
      <button
        onClick={() => logout()}
        className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        Sign out
      </button>
    </header>
  )
}
