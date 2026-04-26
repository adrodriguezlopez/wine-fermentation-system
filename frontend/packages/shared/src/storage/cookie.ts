import Cookies from 'js-cookie'
import type { TokenStorage } from './index'

const ACCESS_TOKEN_KEY = 'wine_access_token'
const REFRESH_TOKEN_KEY = 'wine_refresh_token'

export class CookieTokenStorage implements TokenStorage {
  async getAccessToken(): Promise<string | null> {
    return Cookies.get(ACCESS_TOKEN_KEY) ?? null
  }

  async setAccessToken(token: string): Promise<void> {
    Cookies.set(ACCESS_TOKEN_KEY, token, { sameSite: 'strict' })
  }

  async getRefreshToken(): Promise<string | null> {
    return Cookies.get(REFRESH_TOKEN_KEY) ?? null
  }

  async setRefreshToken(token: string): Promise<void> {
    Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7, sameSite: 'strict' })
  }

  async clear(): Promise<void> {
    Cookies.remove(ACCESS_TOKEN_KEY)
    Cookies.remove(REFRESH_TOKEN_KEY)
  }
}
