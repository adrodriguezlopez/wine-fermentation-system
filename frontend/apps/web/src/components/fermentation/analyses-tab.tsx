"use client"

import Link from 'next/link'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFermentationAnalyses, useTriggerAnalysis } from '@/hooks'

interface Props {
  fermentationId: number
}

export function AnalysesTab({ fermentationId }: Props) {
  const { data, isLoading } = useFermentationAnalyses(fermentationId)
  const { mutate: triggerAnalysis, isPending } = useTriggerAnalysis()

  const analyses = data?.items ?? []

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Analysis History</h3>
        <Button
          size="sm"
          disabled={isPending}
          onClick={() => triggerAnalysis({ fermentation_id: fermentationId })}
        >
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Run Analysis
        </Button>
      </div>

      {isLoading ? (
        <div className="h-16 animate-pulse rounded-md bg-muted" />
      ) : analyses.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No analyses yet — run one to detect anomalies
        </p>
      ) : (
        <div className="space-y-2">
          {analyses.map((analysis: {
            id: string
            analyzed_at: string
            status: string
            anomaly_count: number
            recommendation_count: number
          }) => (
            <Link
              key={analysis.id}
              href={`/fermentations/${fermentationId}/analyses/${analysis.id}`}
              className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm">
                  {new Date(analysis.analyzed_at).toLocaleString()}
                </span>
                <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium">
                  {analysis.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span>{analysis.anomaly_count} {analysis.anomaly_count === 1 ? 'anomaly' : 'anomalies'}</span>
                <span>{analysis.recommendation_count} {analysis.recommendation_count === 1 ? 'recommendation' : 'recommendations'}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
