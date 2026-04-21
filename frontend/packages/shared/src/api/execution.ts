import type { ApiClient } from './client'
import type { ProtocolExecutionDto } from '../types/protocol'

export function createExecutionApi(client: ApiClient) {
  return {
    start(fermentationId: string, protocolId: string): Promise<ProtocolExecutionDto> {
      return client.fermentation
        .post(`/api/v1/fermentations/${fermentationId}/execute`, { protocol_id: protocolId })
        .then(r => r.data)
    },
    get(id: string): Promise<ProtocolExecutionDto> {
      return client.fermentation.get(`/api/v1/executions/${id}`).then(r => r.data)
    },
    list(): Promise<ProtocolExecutionDto[]> {
      return client.fermentation.get('/api/v1/executions').then(r => r.data)
    },
  }
}
