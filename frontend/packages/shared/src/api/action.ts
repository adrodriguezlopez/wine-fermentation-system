import type { ApiClient } from './client'
import type { ActionDto, ActionListResponse } from '../types/action'
import type { ActionFormData, UpdateActionOutcomeData } from '@wine/ui/schemas'

export function createActionApi(client: ApiClient) {
  return {
    create(fermentationId: number, data: ActionFormData): Promise<ActionDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/actions`, data).then(r => r.data)
    },
    listForFermentation(fermentationId: number, params?: { skip?: number; limit?: number }): Promise<ActionListResponse> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/actions`, { params }).then(r => r.data)
    },
    listForExecution(executionId: number, params?: { skip?: number; limit?: number }): Promise<ActionListResponse> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/actions`, { params }).then(r => r.data)
    },
    get(id: number): Promise<ActionDto> {
      return client.fermentation.get(`/api/v1/actions/${id}`).then(r => r.data)
    },
    updateOutcome(id: number, data: UpdateActionOutcomeData): Promise<ActionDto> {
      return client.fermentation.patch(`/api/v1/actions/${id}/outcome`, data).then(r => r.data)
    },
    delete(id: number): Promise<void> {
      return client.fermentation.delete(`/api/v1/actions/${id}`).then(() => undefined)
    },
  }
}

