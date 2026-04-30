import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useExecution(executionId: number | undefined, fermentationStatus?: string) {
  return useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => apiClient.fermentation.get(`/executions/${executionId}`).then(r => r.data),
    enabled: executionId !== undefined,
    refetchInterval: fermentationStatus === 'COMPLETED' ? false : 2 * 60 * 1000,
  })
}

export function useExecutionAlerts(executionId: number | undefined, executionStatus?: string) {
  return useQuery({
    queryKey: ['execution', executionId, 'alerts'],
    queryFn: () => apiClient.fermentation.get(`/executions/${executionId}/alerts`).then(r => r.data),
    enabled: executionId !== undefined,
    refetchInterval: executionStatus === 'COMPLETED' ? false : 2 * 60 * 1000,
  })
}

export function useExecutionCompletions(executionId: number | undefined) {
  return useQuery({
    queryKey: ['execution', executionId, 'completions'],
    queryFn: () => apiClient.fermentation.get(`/executions/${executionId}/completions`).then(r => r.data),
    enabled: executionId !== undefined,
  })
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alertId: number) =>
      apiClient.fermentation.post(`/alerts/${alertId}/acknowledge`).then(r => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['execution'] }),
  })
}

export function useDismissAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alertId: number) =>
      apiClient.fermentation.post(`/alerts/${alertId}/dismiss`).then(r => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['execution'] }),
  })
}

export function useAssignProtocol() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ fermentationId, protocolId }: { fermentationId: number; protocolId: number }) =>
      apiClient.fermentation
        .post(`/fermentations/${fermentationId}/execute`, { protocol_id: protocolId })
        .then(r => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['fermentation', data.fermentation_id] })
    },
  })
}
