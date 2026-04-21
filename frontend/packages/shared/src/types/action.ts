import type { ActionType } from '@wine/ui/schemas'

export interface ActionDto {
  id: string
  fermentation_id: string
  execution_id: string | null
  action_type: ActionType
  description: string
  taken_at: string
  outcome: string | null
  alert_id: string | null
  recommendation_id: string | null
}
