import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useFermentationAnalyses(fermentationId: number) {
  return useQuery({
    queryKey: ['analyses', 'fermentation', fermentationId],
    queryFn: () => apiClient.analysis.get(`/api/v1/analyses/fermentation/${fermentationId}`).then(r => r.data),
  })
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => apiClient.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data),
  })
}

export function useTriggerAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.analysis.post('/api/v1/analyses', data).then(r => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['analyses', 'fermentation', data.fermentation_id] })
    },
  })
}

export function useFermentationAdvisories(fermentationId: number) {
  return useQuery({
    queryKey: ['advisories', 'fermentation', fermentationId],
    queryFn: () => apiClient.analysis.get(`/api/v1/fermentations/${fermentationId}/advisories`).then(r => r.data),
  })
}

export function useApplyRecommendation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.analysis.put(`/api/v1/recommendations/${id}/apply`).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis'] })
    },
  })
}
