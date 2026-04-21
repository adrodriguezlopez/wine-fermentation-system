import type { ApiClient } from './client'
import type { HarvestLotDto } from '../types/vineyard'

export function createHarvestLotApi(client: ApiClient) {
  return {
    list(vineyardId?: string): Promise<HarvestLotDto[]> {
      return client.fruitOrigin
        .get('/api/v1/harvest-lots/', { params: vineyardId ? { vineyard_id: vineyardId } : {} })
        .then(r => r.data)
    },
    get(id: string): Promise<HarvestLotDto> {
      return client.fruitOrigin.get(`/api/v1/harvest-lots/${id}`).then(r => r.data)
    },
    create(data: {
      vineyard_id: string
      vintage_year: number
      variety_name: string
      mass_kg: number
      harvest_date: string
      notes?: string
    }): Promise<HarvestLotDto> {
      return client.fruitOrigin.post('/api/v1/harvest-lots/', data).then(r => r.data)
    },
  }
}
