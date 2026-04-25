import Cookies from 'js-cookie'
import type { TokenStorage } from './index'

const ACCESS_TOKEN_KEY = 'wine_access_token'
const REFRESH_TOKEN_KEY = 'wine_refresh_token'

// Use secure cookies in production (HTTPS); allow plain cookies in local dev
const isSecure = typeof window !== 'undefined' && window.location.protocol === 'https:'

export class CookieTokenStorage implements TokenStorage {
  async getAccessToken(): Promise<string | null> {
    return Cookies.get(ACCESS_TOKEN_KEY) ?? null
  }

  async setAccessToken(token: string): Promise<void> {
    Cookies.set(ACCESS_TOKEN_KEY, token, { sameSite: 'strict', secure: isSecure })
  }

  async getRefreshToken(): Promise<string | null> {
    return Cookies.get(REFRESH_TOKEN_KEY) ?? null
  }

  async setRefreshToken(token: string): Promise<void> {
    Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7, sameSite: 'strict', secure: isSecure })
  }

  async clear(): Promise<void> {
    Cookies.remove(ACCESS_TOKEN_KEY)
    Cookies.remove(REFRESH_TOKEN_KEY)
  }
}

