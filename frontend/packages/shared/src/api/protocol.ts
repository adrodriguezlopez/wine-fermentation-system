import type { ApiClient } from './client'
import type { ProtocolDto, ProtocolListDto } from '../types/protocol'
import type { ProtocolFormData } from '@wine/ui/schemas'

export function createProtocolApi(client: ApiClient) {
  return {
    list(): Promise<ProtocolListDto> {
      return client.fermentation.get('/api/v1/protocols').then(r => r.data)
    },
    get(id: number): Promise<ProtocolDto> {
      return client.fermentation.get(`/api/v1/protocols/${id}`).then(r => r.data)
    },
    create(data: ProtocolFormData): Promise<ProtocolDto> {
      return client.fermentation.post('/api/v1/protocols', data).then(r => r.data)
    },
    update(id: number, data: Partial<ProtocolFormData>): Promise<ProtocolDto> {
      return client.fermentation.patch(`/api/v1/protocols/${id}`, data).then(r => r.data)
    },
    delete(id: number): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${id}`).then(() => undefined)
    },
    clone(id: number): Promise<ProtocolDto> {
      return client.fermentation.post(`/api/v1/protocols/${id}/clone`).then(r => r.data)
    },
  }
}
