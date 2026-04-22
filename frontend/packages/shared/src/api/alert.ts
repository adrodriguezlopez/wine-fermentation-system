import type { ApiClient } from './client'
import type { AlertDto, AlertListResponse } from '../types/alert'

export function createAlertApi(client: ApiClient) {
  return {
    listForExecution(executionId: number): Promise<AlertListResponse> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/alerts`).then(r => r.data)
    },
    acknowledge(alertId: number): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/acknowledge`).then(r => r.data)
    },
    dismiss(alertId: number): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/dismiss`).then(r => r.data)
    },
  }
}
