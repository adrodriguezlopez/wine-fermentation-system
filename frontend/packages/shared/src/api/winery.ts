import type { ApiClient } from './client'
import type { WineryDto, WineryListDto } from '../types/winery'
import type { WineryFormData } from '@wine/ui/schemas'

/** Backend WineryUpdateRequest: name, location, notes only — code is immutable */
type WineryUpdateData = Partial<Pick<WineryFormData, 'name' | 'location' | 'notes'>>

export function createWineryApi(client: ApiClient) {
  return {
    list(): Promise<WineryListDto> {
      return client.winery.get('/api/v1/admin/wineries').then(r => r.data)
    },
    get(id: number): Promise<WineryDto> {
      return client.winery.get(`/api/v1/admin/wineries/${id}`).then(r => r.data)
    },
    create(data: WineryFormData): Promise<WineryDto> {
      return client.winery.post('/api/v1/admin/wineries', data).then(r => r.data)
    },
    update(id: number, data: WineryUpdateData): Promise<WineryDto> {
      return client.winery.patch(`/api/v1/admin/wineries/${id}`, data).then(r => r.data)
    },
    delete(id: number): Promise<void> {
      return client.winery.delete(`/api/v1/admin/wineries/${id}`).then(() => undefined)
    },
  }
}
