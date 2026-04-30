import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useFermentations(filters: { status?: string; search?: string } = {}) {
  return useQuery({
    queryKey: ['fermentations', filters],
    queryFn: () => apiClient.fermentation.get('/api/v1/fermentations', { params: filters }).then(r => r.data),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  })
}

export function useFermentation(id: number) {
  return useQuery({
    queryKey: ['fermentation', id],
    queryFn: () => apiClient.fermentation.get(`/api/v1/fermentations/${id}`).then(r => r.data),
    refetchInterval: 30_000,
  })
}

export function useFermentationStatistics(id: number) {
  return useQuery({
    queryKey: ['fermentation', id, 'statistics'],
    queryFn: () => apiClient.fermentation.get(`/api/v1/fermentations/${id}/statistics`).then(r => r.data),
    refetchInterval: 30_000,
  })
}

export function useCreateFermentation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.fermentation.post('/api/v1/fermentations', data).then(r => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fermentations'] }),
  })
}

export function useFermentationSamples(fermentationId: number, status?: string) {
  return useQuery({
    queryKey: ['fermentation', fermentationId, 'samples'],
    queryFn: () => apiClient.fermentation.get(`/api/v1/fermentations/${fermentationId}/samples`).then(r => r.data),
    refetchInterval: status === 'COMPLETED' ? false : 30_000,
  })
}

export function useLatestSample(fermentationId: number, status?: string) {
  return useQuery({
    queryKey: ['fermentation', fermentationId, 'samples', 'latest'],
    queryFn: () => apiClient.fermentation.get(`/api/v1/fermentations/${fermentationId}/samples/latest`).then(r => r.data),
    refetchInterval: status === 'COMPLETED' ? false : 30_000,
  })
}

export function useRecordSample() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ fermentationId, data }: { fermentationId: number; data: Record<string, unknown> }) =>
      apiClient.fermentation.post(`/api/v1/fermentations/${fermentationId}/samples`, data).then(r => r.data),
    onSuccess: (_, { fermentationId }) => {
      queryClient.invalidateQueries({ queryKey: ['fermentation', fermentationId, 'samples'] })
    },
  })
}

export function useFermentationActions(fermentationId: number) {
  return useQuery({
    queryKey: ['fermentation', fermentationId, 'actions'],
    queryFn: () => apiClient.fermentation.get(`/api/v1/fermentations/${fermentationId}/actions`).then(r => r.data),
  })
}

export function useRecordAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ fermentationId, data }: { fermentationId: number; data: Record<string, unknown> }) =>
      apiClient.fermentation.post(`/api/v1/fermentations/${fermentationId}/actions`, data).then(r => r.data),
    onSuccess: (_, { fermentationId }) => {
      queryClient.invalidateQueries({ queryKey: ['fermentation', fermentationId, 'actions'] })
    },
  })
}

export function useUpdateActionOutcome() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ actionId, data }: { actionId: number; fermentationId: number; data: Record<string, unknown> }) =>
      apiClient.fermentation.patch(`/api/v1/actions/${actionId}/outcome`, data).then(r => r.data),
    onSuccess: (_, { fermentationId }) => {
      queryClient.invalidateQueries({ queryKey: ['fermentation', fermentationId, 'actions'] })
    },
  })
}

export function useProtocols() {
  return useQuery({
    queryKey: ['protocols'],
    queryFn: () => apiClient.fermentation.get('/api/v1/protocols').then(r => r.data),
  })
}
