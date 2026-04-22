import type { ApiClient } from './client'
import type { ProtocolStepDto, ProtocolStepListDto } from '../types/protocol'
import type { ProtocolStepFormData } from '@wine/ui/schemas'

export function createProtocolStepsApi(client: ApiClient) {
  return {
    list(protocolId: number): Promise<ProtocolStepListDto> {
      return client.fermentation.get(`/api/v1/protocols/${protocolId}/steps`).then(r => r.data)
    },
    add(protocolId: number, data: ProtocolStepFormData): Promise<ProtocolStepDto> {
      return client.fermentation.post(`/api/v1/protocols/${protocolId}/steps`, data).then(r => r.data)
    },
    update(protocolId: number, stepId: number, data: Partial<ProtocolStepFormData>): Promise<ProtocolStepDto> {
      return client.fermentation.patch(`/api/v1/protocols/${protocolId}/steps/${stepId}`, data).then(r => r.data)
    },
    delete(protocolId: number, stepId: number): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${protocolId}/steps/${stepId}`).then(() => undefined)
    },
  }
}
