export type AlertType =
  | 'STEP_OVERDUE'
  | 'STEP_DUE_SOON'
  | 'EXECUTION_NEARING_COMPLETION'
  | 'EXECUTION_BEHIND_SCHEDULE'
  | 'CRITICAL_DEVIATION'

export type AlertStatus = 'PENDING' | 'SENT' | 'DISMISSED' | 'ACKNOWLEDGED'

export const ALERT_TYPE_LABEL: Record<AlertType, string> = {
  STEP_OVERDUE: 'Step Overdue',
  STEP_DUE_SOON: 'Step Due Soon',
  EXECUTION_NEARING_COMPLETION: 'Execution Nearing Completion',
  EXECUTION_BEHIND_SCHEDULE: 'Execution Behind Schedule',
  CRITICAL_DEVIATION: 'Critical Deviation',
}

export const ALERT_STATUS_LABEL: Record<AlertStatus, string> = {
  PENDING: 'Pending',
  SENT: 'Sent',
  DISMISSED: 'Dismissed',
  ACKNOWLEDGED: 'Acknowledged',
}
