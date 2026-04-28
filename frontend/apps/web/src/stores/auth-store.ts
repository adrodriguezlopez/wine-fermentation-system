import { create } from 'zustand'
import type { UserDto } from '@wine/shared'

interface AuthState {
  user: UserDto | null
  setUser: (user: UserDto | null) => void
  clearUser: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clearUser: () => set({ user: null }),
}))
