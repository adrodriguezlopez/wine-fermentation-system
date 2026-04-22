export interface DensityReadingRequest {
  /** ISO datetime string (UTC) — maps to backend `timestamp` field */
  timestamp: string
  density: number
}

export interface AnalysisCreateRequest {
  fermentation_id: string
  current_density: number
  temperature_celsius: number
  variety: string
  fruit_origin_id?: string
  starting_brix?: number
  days_fermenting?: number
  previous_densities?: DensityReadingRequest[]
  protocol_compliance_score?: number
}

export interface AnomalyDto {
  id: string
  analysis_id: string
  sample_id: string | null
  anomaly_type: string
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  description: string
  deviation_score: Record<string, unknown>
  is_resolved: boolean
  detected_at: string
  resolved_at: string | null
}

export interface RecommendationDto {
  id: string
  analysis_id: string
  anomaly_id: string | null
  recommendation_template_id: string
  recommendation_text: string
  priority: number
  confidence: number
  supporting_evidence_count: number
  is_applied: boolean
  applied_at: string | null
}

export interface AnalysisDto {
  id: string
  fermentation_id: string
  winery_id: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETE' | 'FAILED'
  analyzed_at: string
  comparison_result: Record<string, unknown>
  confidence_level: Record<string, unknown>
  historical_samples_count: number
  anomalies: AnomalyDto[]
  recommendations: RecommendationDto[]
}

export interface AnalysisSummaryDto {
  id: string
  fermentation_id: string
  status: string
  analyzed_at: string
  historical_samples_count: number
  anomaly_count: number
  recommendation_count: number
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
