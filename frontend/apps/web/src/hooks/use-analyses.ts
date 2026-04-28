import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useFermentationAnalyses(fermentationId: number) {
  return useQuery({
    queryKey: ['analyses', 'fermentation', fermentationId],
    queryFn: () => apiClient.analysis.get(`/analyses/fermentation/${fermentationId}`).then(r => r.data),
  })
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => apiClient.analysis.get(`/analyses/${id}`).then(r => r.data),
  })
}

export function useTriggerAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.analysis.post('/analyses', data).then(r => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['analyses', 'fermentation', data.fermentation_id] })
    },
  })
}
