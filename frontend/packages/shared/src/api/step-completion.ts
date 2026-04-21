import type { ApiClient } from './client'
import type { StepCompletionDto } from '../types/protocol'
import type { StepCompletionFormData } from '@wine/ui/schemas'

export function createStepCompletionApi(client: ApiClient) {
  return {
    complete(executionId: string, data: StepCompletionFormData): Promise<StepCompletionDto> {
      return client.fermentation.post(`/api/v1/executions/${executionId}/complete`, data).then(r => r.data)
    },
    list(executionId: string): Promise<StepCompletionDto[]> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/completions`).then(r => r.data)
    },
    get(id: string): Promise<StepCompletionDto> {
      return client.fermentation.get(`/api/v1/completions/${id}`).then(r => r.data)
    },
  }
}
