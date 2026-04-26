import type { UserRole } from '../types/auth'

export function useRole(role: UserRole | undefined) {
  return {
    role,
    isAdmin: role === 'ADMIN',
    isWinemaker: role === 'WINEMAKER',
    hasRole: (r: UserRole) => role === r,
  }
}
