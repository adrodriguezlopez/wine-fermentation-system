import type { ApiClient } from './client'
import type { SampleDto } from '../types/sample'
import type { SampleFormData } from '@wine/ui/schemas'

export function createSampleApi(client: ApiClient) {
  return {
    create(fermentationId: number, data: SampleFormData): Promise<SampleDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/samples`, data).then(r => r.data)
    },
    list(fermentationId: number): Promise<SampleDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/samples`).then(r => r.data)
    },
    getLatest(fermentationId: number): Promise<SampleDto | null> {
      return client.fermentation
        .get(`/api/v1/fermentations/${fermentationId}/samples/latest`)
        .then(r => r.data)
        .catch(() => null)
    },
  }
}
