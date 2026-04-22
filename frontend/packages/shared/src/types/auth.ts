export type UserRole = 'ADMIN' | 'WINEMAKER'

export interface UserDto {
  id: number
  email: string
  role: UserRole
  winery_id: number
}

export interface LoginResponseDto {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface RefreshResponseDto {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}
