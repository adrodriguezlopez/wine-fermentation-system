import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './auth-store'

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null })
  })

  it('initializes with null user', () => {
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('setUser stores the user', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      role: 'WINEMAKER' as const,
      winery_id: 1,
    }
    useAuthStore.getState().setUser(mockUser)
    expect(useAuthStore.getState().user).toEqual(mockUser)
  })

  it('clearUser resets to null', () => {
    useAuthStore.setState({ user: { id: 1, email: 'test@example.com', role: 'WINEMAKER', winery_id: 1 } })
    useAuthStore.getState().clearUser()
    expect(useAuthStore.getState().user).toBeNull()
  })
})
