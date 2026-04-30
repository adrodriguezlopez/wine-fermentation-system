"use client"

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAnalysis, useFermentationAdvisories, useApplyRecommendation } from '@/hooks'

interface Props {
  params: { id: string; aid: string }
}

export default function AnalysisDetailPage({ params }: Props) {
  const fermentationId = parseInt(params.id, 10)
  const { data: analysis, isLoading, isError } = useAnalysis(params.aid)
  const { data: advisories } = useFermentationAdvisories(fermentationId)
  const { mutate: applyRecommendation, isPending: isApplying } = useApplyRecommendation()

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded bg-muted" />
      </div>
    )
  }

  if (isError || !analysis) {
    return (
      <div className="space-y-4">
        <p className="text-destructive">Analysis not found</p>
        <Link href={`/fermentations/${params.id}`} className="text-sm text-muted-foreground underline">
          Back to fermentation
        </Link>
      </div>
    )
  }

  const anomalies: Array<{
    id: string
    anomaly_type: string
    severity: string
    description: string
    detected_at: string
  }> = analysis.anomalies ?? []

  const recommendations: Array<{
    id: string
    recommendation_type: string
    priority: string
    description: string
    applied: boolean
    applied_at: string | null
  }> = analysis.recommendations ?? []

  const advisoryList: Array<{
    id: string
    advisory_type: string
    message: string
    created_at: string
  }> = advisories ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href={`/fermentations/${params.id}`}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-semibold">Analysis Detail</h1>
      </div>

      {/* Anomalies */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">Anomalies</h2>
        {anomalies.length === 0 ? (
          <p className="text-sm text-muted-foreground">No anomalies detected</p>
        ) : (
          <div className="space-y-2">
            {anomalies.map((anomaly) => (
              <div key={anomaly.id} className="rounded-md border p-3 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{anomaly.anomaly_type}</span>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium">
                    {anomaly.severity}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{anomaly.description}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recommendations */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">Recommendations</h2>
        {recommendations.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recommendations</p>
        ) : (
          <div className="space-y-2">
            {recommendations.map((rec) => (
              <div key={rec.id} className="rounded-md border p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{rec.recommendation_type}</span>
                    <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium">
                      {rec.priority}
                    </span>
                  </div>
                  {rec.applied ? (
                    <span className="text-sm text-green-600">Applied ✓</span>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={isApplying}
                      onClick={() => applyRecommendation(rec.id)}
                    >
                      Apply
                    </Button>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{rec.description}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Advisories */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">Advisories</h2>
        {advisoryList.length === 0 ? (
          <p className="text-sm text-muted-foreground">No advisories</p>
        ) : (
          <div className="space-y-2">
            {advisoryList.map((advisory) => (
              <div key={advisory.id} className="rounded-md border p-3 space-y-1">
                <span className="text-sm font-medium">{advisory.advisory_type}</span>
                <p className="text-sm text-muted-foreground">{advisory.message}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
