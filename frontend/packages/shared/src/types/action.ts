import type { ActionType } from '@wine/ui/schemas'

export interface ActionDto {
  id: number
  winery_id: number
  taken_by_user_id: number
  fermentation_id: number | null
  execution_id: number | null
  step_id: number | null
  alert_id: number | null
  recommendation_id: number | null
  action_type: ActionType
  description: string
  taken_at: string
  outcome: string
  outcome_notes: string | null
  outcome_recorded_at: string | null
  created_at: string
  updated_at: string
}

export interface ActionListResponse {
  items: ActionDto[]
  total: number
  skip: number
  limit: number
}
