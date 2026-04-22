import type { AlertType, AlertStatus } from '@wine/ui/constants'

export interface AlertDto {
  id: number
  execution_id: number
  protocol_id: number
  winery_id: number
  step_id: number | null
  step_name: string | null
  alert_type: AlertType
  severity: string           // 'INFO' | 'WARNING' | 'CRITICAL'
  status: AlertStatus
  message: string
  created_at: string
  sent_at: string | null
  acknowledged_at: string | null
  dismissed_at: string | null
}

export interface AlertListResponse {
  items: AlertDto[]
  total: number
  pending_count: number
}
