import type { ApiClient } from './client'
import type { FermentationDto, PaginatedResponse, FermentationStatisticsDto } from '../types/fermentation'
import type { CreateFermentationData, BlendFermentationData, UpdateFermentationData } from '@wine/ui/schemas'

export function createFermentationApi(client: ApiClient) {
  return {
    list(params?: { page?: number; size?: number; status?: string }): Promise<PaginatedResponse<FermentationDto>> {
      return client.fermentation.get('/api/v1/fermentations', { params }).then(r => r.data)
    },
    get(id: string): Promise<FermentationDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}`).then(r => r.data)
    },
    create(data: CreateFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations', data).then(r => r.data)
    },
    createBlend(data: BlendFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations/blends', data).then(r => r.data)
    },
    update(id: string, data: UpdateFermentationData): Promise<FermentationDto> {
      return client.fermentation.patch(`/api/v1/fermentations/${id}`, data).then(r => r.data)
    },
    complete(id: string): Promise<FermentationDto> {
      return client.fermentation.post(`/api/v1/fermentations/${id}/complete`).then(r => r.data)
    },
    getStatistics(id: string): Promise<FermentationStatisticsDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/statistics`).then(r => r.data)
    },
    getTimeline(id: string): Promise<unknown[]> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/timeline`).then(r => r.data)
    },
  }
}
