export type UserRole = 'ADMIN' | 'WINEMAKER'

export interface UserDto {
  id: number
  email: string
  role: UserRole
  winery_id: string
}

export interface LoginResponseDto {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RefreshResponseDto {
  access_token: string
  token_type: 'bearer'
}
