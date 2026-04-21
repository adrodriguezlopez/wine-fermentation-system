import type { ApiClient } from './client'
import type { AdvisoryDto } from '../types/analysis'

export function createAdvisoryApi(client: ApiClient) {
  return {
    listForFermentation(fermentationId: string): Promise<AdvisoryDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/advisories`).then(r => r.data)
    },
    acknowledge(id: string): Promise<AdvisoryDto> {
      return client.analysis.post(`/api/v1/advisories/${id}/acknowledge`).then(r => r.data)
    },
  }
}
