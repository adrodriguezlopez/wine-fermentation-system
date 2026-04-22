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
  id: string                   // UUID
  fermentation_id: string      // UUID
  analysis_id: string          // UUID
  execution_id: string | null  // UUID
  advisory_type: string        // ACCELERATE_STEP | SKIP_STEP | ADD_STEP
  target_step_type: string
  risk_level: string           // CRITICAL | HIGH | MEDIUM | LOW
  suggestion: string
  reasoning: string
  confidence: number           // 0-1
  is_acknowledged: boolean
  acknowledged_at: string | null
  created_at: string
}

export interface AdvisoryListDto {
  items: AdvisoryDto[]
  total: number
  unacknowledged_count: number
}
