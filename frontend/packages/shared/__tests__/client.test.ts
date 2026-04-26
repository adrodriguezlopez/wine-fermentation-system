import { describe, it, expect, vi } from 'vitest'
import { ApiClient, AuthExpiredError } from '../src/api/client'
import type { TokenStorage } from '../src/storage/index'

const makeStorage = (accessToken: string | null = 'test-token'): TokenStorage => ({
  getAccessToken: vi.fn().mockResolvedValue(accessToken),
  setAccessToken: vi.fn().mockResolvedValue(undefined),
  getRefreshToken: vi.fn().mockResolvedValue('refresh-token'),
  setRefreshToken: vi.fn().mockResolvedValue(undefined),
  clear: vi.fn().mockResolvedValue(undefined),
})

describe('ApiClient', () => {
  it('can be instantiated with base URLs and storage', () => {
    const client = new ApiClient({
      baseURLs: {
        fermentation: 'http://localhost:8000',
        winery: 'http://localhost:8001',
        fruitOrigin: 'http://localhost:8002',
        analysis: 'http://localhost:8003',
      },
      tokenStorage: makeStorage(),
    })
    expect(client).toBeDefined()
    expect(client.fermentation).toBeDefined()
    expect(client.winery).toBeDefined()
    expect(client.fruitOrigin).toBeDefined()
    expect(client.analysis).toBeDefined()
  })

  it('exports AuthExpiredError', () => {
    expect(AuthExpiredError).toBeDefined()
    const err = new AuthExpiredError()
    expect(err).toBeInstanceOf(Error)
    expect(err.message).toBe('Authentication expired')
  })
})
