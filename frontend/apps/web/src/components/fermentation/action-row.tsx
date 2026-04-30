"use client"
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ACTION_TYPE_LABEL } from '@wine/ui'
import type { ActionDto } from '@wine/shared'
import type { ActionType } from '@wine/ui'

interface Props { action: ActionDto; onUpdateOutcome?: (actionId: number, outcome: string) => void }

export function ActionRow({ action, onUpdateOutcome }: Props) {
  const [showOutcome, setShowOutcome] = useState(false)
  return (
    <div className="rounded-md border p-3 space-y-1 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium">{ACTION_TYPE_LABEL[action.action_type as ActionType] ?? action.action_type}</span>
        <span className="text-xs text-muted-foreground">{new Date(action.taken_at).toLocaleString()}</span>
      </div>
      <p>{action.description}</p>
      {action.outcome && action.outcome !== 'PENDING' && (
        <p className="text-xs text-muted-foreground">Outcome: {action.outcome}</p>
      )}
      <Button variant="outline" size="sm" onClick={() => setShowOutcome(!showOutcome)}>
        Update Outcome
      </Button>
      {showOutcome && (
        <select
          className="block w-full rounded border p-1 text-xs"
          defaultValue={action.outcome}
          onChange={(e) => { onUpdateOutcome?.(action.id, e.target.value); setShowOutcome(false) }}
        >
          <option value="PENDING">Pending</option>
          <option value="RESOLVED">Resolved</option>
          <option value="NO_EFFECT">No Effect</option>
          <option value="WORSENED">Worsened</option>
        </select>
      )}
    </div>
  )
}
