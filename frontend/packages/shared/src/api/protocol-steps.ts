import type { ApiClient } from './client'
import type { ProtocolStepDto } from '../types/protocol'
import type { ProtocolStepFormData } from '@wine/ui/schemas'

export function createProtocolStepsApi(client: ApiClient) {
  return {
    list(protocolId: string): Promise<ProtocolStepDto[]> {
      return client.fermentation.get(`/api/v1/protocols/${protocolId}/steps`).then(r => r.data)
    },
    add(protocolId: string, data: ProtocolStepFormData): Promise<ProtocolStepDto> {
      return client.fermentation.post(`/api/v1/protocols/${protocolId}/steps`, data).then(r => r.data)
    },
    update(protocolId: string, stepId: string, data: Partial<ProtocolStepFormData>): Promise<ProtocolStepDto> {
      return client.fermentation.patch(`/api/v1/protocols/${protocolId}/steps/${stepId}`, data).then(r => r.data)
    },
    delete(protocolId: string, stepId: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${protocolId}/steps/${stepId}`).then(() => undefined)
    },
  }
}
