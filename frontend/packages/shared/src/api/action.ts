import type { ApiClient } from './client'
import type { ActionDto } from '../types/action'
import type { ActionFormData, UpdateActionOutcomeData } from '@wine/ui/schemas'

export function createActionApi(client: ApiClient) {
  return {
    create(fermentationId: string, data: ActionFormData): Promise<ActionDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/actions`, data).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<ActionDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/actions`).then(r => r.data)
    },
    updateOutcome(id: string, data: UpdateActionOutcomeData): Promise<ActionDto> {
      return client.fermentation.patch(`/api/v1/actions/${id}/outcome`, data).then(r => r.data)
    },
  }
}
