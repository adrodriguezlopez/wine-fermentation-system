import type { ApiClient } from './client'
import type { HarvestLotDto, HarvestLotListDto } from '../types/vineyard'

export function createHarvestLotApi(client: ApiClient) {
  return {
    list(vineyardId?: number): Promise<HarvestLotListDto> {
      return client.fruitOrigin
        .get('/api/v1/harvest-lots/', { params: vineyardId !== undefined ? { vineyard_id: vineyardId } : {} })
        .then(r => r.data)
    },
    get(id: number): Promise<HarvestLotDto> {
      return client.fruitOrigin.get(`/api/v1/harvest-lots/${id}`).then(r => r.data)
    },
    create(data: {
      block_id: number
      code: string
      harvest_date: string
      weight_kg: number
      brix_at_harvest?: number
      brix_method?: string
      grape_variety?: string
      clone?: string
      rootstock?: string
      pick_method?: string
      bins_count?: number
      field_temp_c?: number
      notes?: string
    }): Promise<HarvestLotDto> {
      return client.fruitOrigin.post('/api/v1/harvest-lots/', data).then(r => r.data)
    },
  }
}
