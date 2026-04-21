import type { AlertType, AlertStatus } from '@wine/ui/constants'

export interface AlertDto {
  id: string
  execution_id: string
  alert_type: AlertType
  status: AlertStatus
  message: string
  created_at: string
  acknowledged_at: string | null
  dismissed_at: string | null
}
