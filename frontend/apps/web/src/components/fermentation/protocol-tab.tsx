"use client"
import { useState } from 'react'
import { useExecution, useExecutionCompletions, useProtocols, useAssignProtocol } from '@/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CheckCircle, Clock, XCircle } from 'lucide-react'

interface Props {
  fermentationId: number
  executionId: number | undefined
}

export function ProtocolTab({ fermentationId, executionId }: Props) {
  const [showAssign, setShowAssign] = useState(false)
  const [selectedProtocolId, setSelectedProtocolId] = useState<string>('')
  const { data: execution } = useExecution(executionId)
  const { data: completionsData } = useExecutionCompletions(executionId)
  const { data: protocolsData } = useProtocols()
  const { mutate: assignProtocol, isPending } = useAssignProtocol()
  const protocols = protocolsData?.items ?? []
  const completions = completionsData?.items ?? []

  if (!executionId || !execution) {
    return (
      <div className="space-y-3 pt-4">
        <p className="text-sm text-muted-foreground">No protocol assigned to this fermentation.</p>
        {!showAssign ? (
          <Button variant="outline" onClick={() => setShowAssign(true)}>
            Assign a protocol to this fermentation
          </Button>
        ) : (
          <div className="flex gap-2">
            <Select value={selectedProtocolId} onValueChange={setSelectedProtocolId}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select protocol..." />
              </SelectTrigger>
              <SelectContent>
                {protocols.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.protocol_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              disabled={!selectedProtocolId || isPending}
              onClick={() => {
                if (selectedProtocolId) {
                  assignProtocol({ fermentationId, protocolId: parseInt(selectedProtocolId, 10) })
                  setShowAssign(false)
                }
              }}
            >
              {isPending ? 'Assigning...' : 'Confirm'}
            </Button>
            <Button variant="outline" onClick={() => setShowAssign(false)}>Cancel</Button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center gap-3">
        <h3 className="font-medium">Protocol Execution</h3>
        <Badge>{execution.status}</Badge>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-muted-foreground">Start Date:</span> {new Date(execution.start_date).toLocaleDateString()}</div>
        <div><span className="text-muted-foreground">Progress:</span> {execution.completion_percentage}%</div>
        <div><span className="text-muted-foreground">Compliance:</span> {execution.compliance_score}%</div>
      </div>
      {completions.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Step Completions</h4>
          <div className="space-y-2">
            {completions.map((c) => (
              <div key={c.id} className="flex items-center gap-2 rounded-md border p-2 text-sm">
                {c.was_skipped ? (
                  <XCircle className="h-4 w-4 text-red-500" />
                ) : c.completed_at ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <Clock className="h-4 w-4 text-muted-foreground" />
                )}
                <span>Step {c.step_id}</span>
                {c.days_late > 0 && <span className="text-red-500">({c.days_late}d late)</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
