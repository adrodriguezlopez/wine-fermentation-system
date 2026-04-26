import type { ApiClient } from './client'
import type { AnalysisDto, AnalysisSummaryDto, AnalysisCreateRequest } from '../types/analysis'
import type { PaginatedResponse } from '../types/fermentation'

export function createAnalysisApi(client: ApiClient) {
  return {
    trigger(data: AnalysisCreateRequest): Promise<AnalysisDto> {
      return client.analysis.post('/api/v1/analyses', data).then(r => r.data)
    },
    get(id: string): Promise<AnalysisDto> {
      return client.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<PaginatedResponse<AnalysisSummaryDto>> {
      return client.analysis.get(`/api/v1/analyses/fermentation/${fermentationId}`).then(r => r.data)
    },
  }
}
