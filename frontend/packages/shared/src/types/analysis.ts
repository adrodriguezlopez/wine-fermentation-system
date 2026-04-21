import type { ConfidenceLevel } from '@wine/ui/constants'

export interface AnalysisDto {
  id: string
  fermentation_id: string
  winery_id: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  overall_confidence: ConfidenceLevel | null
  created_at: string
  completed_at: string | null
}

export interface AnomalyDto {
  id: string
  analysis_id: string
  anomaly_type: string
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  description: string
  detected_at: string
}

export interface RecommendationDto {
  id: string
  analysis_id: string
  category: string
  title: string
  description: string
  applied: boolean
  applied_at: string | null
}

export interface AdvisoryDto {
  id: string
  fermentation_id: string
  message: string
  acknowledged: boolean
  created_at: string
}
