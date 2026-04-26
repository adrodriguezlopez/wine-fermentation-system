import type { ApiClient } from './client'
import type { RecommendationDto } from '../types/analysis'

export function createRecommendationApi(client: ApiClient) {
  return {
    get(id: string): Promise<RecommendationDto> {
      return client.analysis.get(`/api/v1/recommendations/${id}`).then(r => r.data)
    },
    apply(id: string, notes?: string): Promise<RecommendationDto> {
      return client.analysis.put(`/api/v1/recommendations/${id}/apply`, { notes }).then(r => r.data)
    },
  }
}
