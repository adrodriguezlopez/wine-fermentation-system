import type { ApiClient } from './client'
import type { AnalysisDto } from '../types/analysis'

export function createAnalysisApi(client: ApiClient) {
  return {
    trigger(fermentationId: string): Promise<AnalysisDto> {
      return client.analysis.post('/api/v1/analyses', { fermentation_id: fermentationId }).then(r => r.data)
    },
    get(id: string): Promise<AnalysisDto> {
      return client.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<AnalysisDto[]> {
      return client.analysis.get(`/api/v1/analyses/fermentation/${fermentationId}`).then(r => r.data)
    },
  }
}
