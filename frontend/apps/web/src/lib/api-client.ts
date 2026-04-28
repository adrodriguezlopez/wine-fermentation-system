import { ApiClient, CookieTokenStorage } from '@wine/shared'

export const apiClient = new ApiClient({
  tokenStorage: new CookieTokenStorage(),
  baseURLs: {
    fermentation: '/api/fermentation',
    winery: '/api/winery',
    fruitOrigin: '/api/fruit-origin',
    analysis: '/api/analysis',
  },
})
