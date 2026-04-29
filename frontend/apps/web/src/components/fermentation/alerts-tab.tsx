"use client"
import { useExecutionAlerts, useAcknowledgeAlert, useDismissAlert } from '@/hooks'
import { AlertRow } from './alert-row'

interface Props {
  executionId: number | undefined
  executionStatus?: string
}

export function AlertsTab({ executionId, executionStatus }: Props) {
  const { data: alertsData, isLoading } = useExecutionAlerts(executionId, executionStatus)
  const { mutate: acknowledge } = useAcknowledgeAlert()
  const { mutate: dismiss } = useDismissAlert()

  if (!executionId) {
    return (
      <div className="pt-4 text-sm text-muted-foreground">
        No protocol assigned — alerts will appear here once a protocol is running.
      </div>
    )
  }

  const alerts = alertsData?.items ?? []
  const isCompleted = executionStatus === 'COMPLETED'

  return (
    <div className="space-y-3 pt-4">
      {isCompleted && (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
          Protocol completed — showing historical alerts.
        </div>
      )}
      {isLoading ? (
        <div className="h-16 animate-pulse rounded-md bg-muted" />
      ) : alerts.length === 0 ? (
        <p className="text-sm text-muted-foreground">No alerts.</p>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <AlertRow key={alert.id} alert={alert} onAcknowledge={acknowledge} onDismiss={dismiss} />
          ))}
        </div>
      )}
    </div>
  )
}
