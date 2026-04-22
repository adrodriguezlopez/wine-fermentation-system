import type { ApiClient } from './client'
import type { StepCompletionDto, StepCompletionListDto, CompletionCreateRequest } from '../types/protocol'

export function createStepCompletionApi(client: ApiClient) {
  return {
    complete(executionId: number, data: CompletionCreateRequest): Promise<StepCompletionDto> {
      return client.fermentation.post(`/api/v1/executions/${executionId}/complete`, data).then(r => r.data)
    },
    list(executionId: number): Promise<StepCompletionListDto> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/completions`).then(r => r.data)
    },
    get(id: number): Promise<StepCompletionDto> {
      return client.fermentation.get(`/api/v1/completions/${id}`).then(r => r.data)
    },
  }
}
