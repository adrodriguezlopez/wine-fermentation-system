import type { ApiClient } from './client'
import type { AdvisoryDto, AdvisoryListDto } from '../types/analysis'

export function createAdvisoryApi(client: ApiClient) {
  return {
    listForFermentation(
      fermentationId: string,  // UUID
      params?: { include_acknowledged?: boolean; skip?: number; limit?: number }
    ): Promise<AdvisoryListDto> {
      return client.analysis.get(`/api/v1/fermentations/${fermentationId}/advisories`, { params }).then(r => r.data)
    },
    acknowledge(id: string): Promise<AdvisoryDto> {
      return client.analysis.post(`/api/v1/advisories/${id}/acknowledge`).then(r => r.data)
    },
  }
}
