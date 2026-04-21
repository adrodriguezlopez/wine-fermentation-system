import type { ApiClient } from './client'
import type { VineyardDto } from '../types/vineyard'

export function createVineyardApi(client: ApiClient) {
  return {
    list(): Promise<VineyardDto[]> {
      return client.fruitOrigin.get('/api/v1/vineyards/').then(r => r.data)
    },
    get(id: string): Promise<VineyardDto> {
      return client.fruitOrigin.get(`/api/v1/vineyards/${id}`).then(r => r.data)
    },
    create(data: { name: string; location?: string; hectares?: number }): Promise<VineyardDto> {
      return client.fruitOrigin.post('/api/v1/vineyards/', data).then(r => r.data)
    },
    update(id: string, data: Partial<{ name: string; location: string; hectares: number }>): Promise<VineyardDto> {
      return client.fruitOrigin.patch(`/api/v1/vineyards/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fruitOrigin.delete(`/api/v1/vineyards/${id}`).then(() => undefined)
    },
  }
}
