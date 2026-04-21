export interface ProtocolDto {
  id: string
  winery_id: string
  varietal_code: string
  varietal_name: string
  version: string
  expected_duration_days: number
  description: string | null
  created_at: string
}

export interface ProtocolStepDto {
  id: string
  protocol_id: string
  step_type: string
  sequence: number
  duration_hours: number
  threshold_values: Record<string, number> | null
  notes: string | null
}

export interface ProtocolExecutionDto {
  id: string
  fermentation_id: string
  protocol_id: string
  status: 'ACTIVE' | 'COMPLETED' | 'ABANDONED'
  started_at: string
  completed_at: string | null
}

export interface StepCompletionDto {
  id: string
  execution_id: string
  step_id: string
  completed_by: number
  completion_date: string
  notes: string | null
}
