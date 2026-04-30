"use client"
import { BellOff, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { AlertDto } from '@wine/shared'

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: '#DC2626',
  WARNING: '#D97706',
  INFO: '#2563EB',
}

interface Props {
  alert: AlertDto
  onAcknowledge: (id: number) => void
  onDismiss: (id: number) => void
}

export function AlertRow({ alert, onAcknowledge, onDismiss }: Props) {
  const isAcknowledged = alert.acknowledged_at != null
  return (
    <div className={cn('flex items-start gap-3 rounded-md border p-3', isAcknowledged && 'opacity-60')}>
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <Badge style={{ backgroundColor: SEVERITY_COLOR[alert.severity] ?? '#6B7280', color: '#fff' }}>
            {alert.severity}
          </Badge>
          {isAcknowledged && <BellOff className="h-3 w-3 text-muted-foreground" aria-label="acknowledged" />}
        </div>
        <p className="text-sm">{alert.message}</p>
        <p className="text-xs text-muted-foreground">{new Date(alert.created_at).toLocaleString()}</p>
      </div>
      <div className="flex shrink-0 gap-1">
        <Button variant="outline" size="sm" onClick={() => onAcknowledge(alert.id)}>
          Acknowledge
        </Button>
        <Button variant="outline" size="sm" onClick={() => onDismiss(alert.id)}>
          Dismiss
        </Button>
      </div>
    </div>
  )
}
