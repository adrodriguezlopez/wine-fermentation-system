import type { ApiClient } from './client'
import type { AnalysisDto, AnalysisSummaryDto, AnalysisCreateRequest } from '../types/analysis'

export function createAnalysisApi(client: ApiClient) {
  return {
    trigger(data: AnalysisCreateRequest): Promise<AnalysisDto> {
      return client.analysis.post('/api/v1/analyses', data).then(r => r.data)
    },
    get(id: string): Promise<AnalysisDto> {
      return client.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data)
    },
    /** Returns plain array (most recent first) — backend returns List[AnalysisSummaryResponse], not paginated */
    listForFermentation(fermentationId: string, limit = 10): Promise<AnalysisSummaryDto[]> {
      return client.analysis
        .get(`/api/v1/analyses/fermentation/${fermentationId}`, { params: { limit } })
        .then(r => r.data)
    },
  }
}
