import type { ApiClient } from './client'
import type { ProtocolDto } from '../types/protocol'
import type { ProtocolFormData } from '@wine/ui/schemas'

export function createProtocolApi(client: ApiClient) {
  return {
    list(): Promise<ProtocolDto[]> {
      return client.fermentation.get('/api/v1/protocols').then(r => r.data)
    },
    get(id: string): Promise<ProtocolDto> {
      return client.fermentation.get(`/api/v1/protocols/${id}`).then(r => r.data)
    },
    create(data: ProtocolFormData): Promise<ProtocolDto> {
      return client.fermentation.post('/api/v1/protocols', data).then(r => r.data)
    },
    update(id: string, data: Partial<ProtocolFormData>): Promise<ProtocolDto> {
      return client.fermentation.patch(`/api/v1/protocols/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${id}`).then(() => undefined)
    },
    clone(id: string): Promise<ProtocolDto> {
      return client.fermentation.post(`/api/v1/protocols/${id}/clone`).then(r => r.data)
    },
  }
}
