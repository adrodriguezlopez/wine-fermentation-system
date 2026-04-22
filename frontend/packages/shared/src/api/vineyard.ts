import type { ApiClient } from './client'
import type { VineyardDto, VineyardListDto } from '../types/vineyard'

export function createVineyardApi(client: ApiClient) {
  return {
    list(): Promise<VineyardListDto> {
      return client.fruitOrigin.get('/api/v1/vineyards/').then(r => r.data)
    },
    get(id: number): Promise<VineyardDto> {
      return client.fruitOrigin.get(`/api/v1/vineyards/${id}`).then(r => r.data)
    },
    create(data: { code: string; name: string; notes?: string }): Promise<VineyardDto> {
      return client.fruitOrigin.post('/api/v1/vineyards/', data).then(r => r.data)
    },
    update(id: number, data: Partial<{ code: string; name: string; notes: string }>): Promise<VineyardDto> {
      return client.fruitOrigin.patch(`/api/v1/vineyards/${id}`, data).then(r => r.data)
    },
    delete(id: number): Promise<void> {
      return client.fruitOrigin.delete(`/api/v1/vineyards/${id}`).then(() => undefined)
    },
  }
}
