export interface ProtocolDto {
  id: number
  winery_id: number
  varietal_code: string
  varietal_name: string
  color: string
  version: string
  protocol_name: string
  is_active: boolean
  expected_duration_days: number
  description: string | null
  is_template: boolean | null
  state: 'DRAFT' | 'FINAL' | 'DEPRECATED' | null
  template_id: number | null
  approved_by_user_id: number | null
  created_at: string
  updated_at: string
}

export interface ProtocolListDto {
  items: ProtocolDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProtocolStepDto {
  id: number
  protocol_id: number
  step_order: number
  step_type: string
  description: string
  expected_day: number
  tolerance_hours: number
  duration_minutes: number
  criticality_score: number
  can_repeat_daily: boolean
  depends_on_step_id: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ProtocolStepListDto {
  items: ProtocolStepDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProtocolExecutionDto {
  id: number
  fermentation_id: number
  protocol_id: number
  winery_id: number
  status: string
  start_date: string
  completion_percentage: number
  compliance_score: number
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ExecutionListDto {
  items: ProtocolExecutionDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface StepCompletionDto {
  id: number
  execution_id: number
  step_id: number
  winery_id: number
  was_skipped: boolean
  completed_at: string | null
  is_on_schedule: boolean
  days_late: number
  skip_reason: string | null
  skip_notes: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface StepCompletionListDto {
  items: StepCompletionDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface CompletionCreateRequest {
  step_id: number
  was_skipped?: boolean
  completed_at?: string
  is_on_schedule?: boolean
  days_late?: number
  skip_reason?: string
  skip_notes?: string
  notes?: string
}
