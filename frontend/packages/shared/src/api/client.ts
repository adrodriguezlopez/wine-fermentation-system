import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import type { TokenStorage } from '../storage/index'
import type { LoginResponseDto, RefreshResponseDto, UserDto } from '../types/auth'

export class AuthExpiredError extends Error {
  constructor() {
    super('Authentication expired')
    this.name = 'AuthExpiredError'
  }
}

interface ApiClientConfig {
  baseURLs: {
    fermentation: string
    winery: string
    fruitOrigin: string
    analysis: string
  }
  tokenStorage: TokenStorage
}

export class ApiClient {
  public fermentation: AxiosInstance
  public winery: AxiosInstance
  public fruitOrigin: AxiosInstance
  public analysis: AxiosInstance

  private tokenStorage: TokenStorage
  private isRefreshing = false
  private refreshSubscribers: Array<{ resolve: (token: string) => void; reject: (err: Error) => void }> = []

  constructor(config: ApiClientConfig) {
    this.tokenStorage = config.tokenStorage
    this.fermentation = this.createInstance(config.baseURLs.fermentation)
    this.winery = this.createInstance(config.baseURLs.winery)
    this.fruitOrigin = this.createInstance(config.baseURLs.fruitOrigin)
    this.analysis = this.createInstance(config.baseURLs.analysis)
  }

  private createInstance(baseURL: string): AxiosInstance {
    const instance = axios.create({ baseURL })

    instance.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
      const token = await this.tokenStorage.getAccessToken()
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    })

    instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise<string>((resolve, reject) => {
              this.refreshSubscribers.push({ resolve, reject })
            }).then((token) => {
              originalRequest.headers = {
                ...originalRequest.headers,
                Authorization: `Bearer ${token}`,
              }
              return instance(originalRequest)
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const refreshToken = await this.tokenStorage.getRefreshToken()
            const response = await axios.post<RefreshResponseDto>(
              `${this.fermentation.defaults.baseURL}/api/v1/auth/refresh`,
              { refresh_token: refreshToken }
            )
            const newToken = response.data.access_token
            await this.tokenStorage.setAccessToken(newToken)

            this.refreshSubscribers.forEach(({ resolve }) => resolve(newToken))
            this.refreshSubscribers = []
            this.isRefreshing = false

            originalRequest.headers = {
              ...originalRequest.headers,
              Authorization: `Bearer ${newToken}`,
            }
            return instance(originalRequest)
          } catch {
            this.isRefreshing = false
            const err = new AuthExpiredError()
            this.refreshSubscribers.forEach(({ reject }) => reject(err))
            this.refreshSubscribers = []
            await this.tokenStorage.clear()
            throw new AuthExpiredError()
          }
        }
        return Promise.reject(error)
      }
    )

    return instance
  }

  async login(username: string, password: string): Promise<LoginResponseDto> {
    const response = await this.fermentation.post<LoginResponseDto>(
      '/api/v1/auth/login',
      { username, password }
    )
    await this.tokenStorage.setAccessToken(response.data.access_token)
    await this.tokenStorage.setRefreshToken(response.data.refresh_token)
    return response.data
  }

  async logout(): Promise<void> {
    await this.tokenStorage.clear()
  }

  async getCurrentUser(): Promise<UserDto> {
    const response = await this.fermentation.get<UserDto>('/api/v1/auth/me')
    return response.data
  }
}
