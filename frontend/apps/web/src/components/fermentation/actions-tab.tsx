"use client"
import { useFermentationActions, useUpdateActionOutcome } from '@/hooks'
import { ActionRow } from './action-row'
import { RecordActionForm } from './record-action-form'
import type { FermentationDto } from '@wine/shared'

interface Props { fermentation: FermentationDto }

export function ActionsTab({ fermentation }: Props) {
  const { data: actionsData, isLoading } = useFermentationActions(fermentation.id)
  const { mutate: updateOutcome } = useUpdateActionOutcome()
  const actions = actionsData?.items ?? []

  return (
    <div className="space-y-6 pt-4">
      <div>
        <h3 className="mb-3 text-sm font-medium">Record Action</h3>
        <RecordActionForm fermentationId={fermentation.id} />
      </div>
      <div>
        <h3 className="mb-3 text-sm font-medium">Action Log</h3>
        {isLoading ? (
          <div className="h-16 animate-pulse rounded-md bg-muted" />
        ) : actions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No actions recorded</p>
        ) : (
          <div className="space-y-2">
            {actions.map((action) => (
              <ActionRow
                key={action.id}
                action={action}
                onUpdateOutcome={(actionId, outcome) =>
                  updateOutcome({ actionId, fermentationId: fermentation.id, data: { outcome } })
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
