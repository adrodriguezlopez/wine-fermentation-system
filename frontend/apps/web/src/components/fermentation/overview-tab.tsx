"use client"

import { formatDensity, formatCelsius } from '@wine/ui'
import { useLatestSample, useFermentationSamples, useFermentationStatistics } from '@/hooks'
import { DensityChart } from './density-chart'
import type { FermentationDto } from '@wine/shared'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Props {
  fermentation: FermentationDto
}

export function OverviewTab({ fermentation }: Props) {
  const { data: latestSample } = useLatestSample(fermentation.id, fermentation.status)
  const { data: samples = [] } = useFermentationSamples(fermentation.id, fermentation.status)
  const { data: stats } = useFermentationStatistics(fermentation.id)

  const daysActive = fermentation.start_date
    ? Math.floor((Date.now() - new Date(
        fermentation.start_date.endsWith('Z') ? fermentation.start_date : fermentation.start_date + 'Z'
      ).getTime()) / (1000 * 60 * 60 * 24))
    : null

  return (
    <div className="space-y-4 pt-4">
      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-muted-foreground">Vintage Year</p>
          <p className="font-medium">{fermentation.vintage_year}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Yeast Strain</p>
          <p className="font-medium">{fermentation.yeast_strain}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Mass (kg)</p>
          <p className="font-medium">{fermentation.input_mass_kg}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Days Active</p>
          <p className="font-medium">{daysActive ?? '—'}</p>
        </div>
      </div>

      {/* Latest sample */}
      {latestSample && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Latest Measurement</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {latestSample.sample_type === 'density'
                ? formatDensity(latestSample.value)
                : latestSample.sample_type === 'temperature'
                ? formatCelsius(latestSample.value)
                : `${latestSample.value} ${latestSample.units}`}
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(latestSample.recorded_at).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Density chart */}
      <div>
        <h3 className="mb-2 text-sm font-medium">Density Trend</h3>
        <DensityChart samples={samples} />
      </div>

      {/* Statistics */}
      {stats && (
        <div>
          <h3 className="mb-2 text-sm font-medium">Statistics</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">Total Samples</p>
              <p className="font-medium">{stats.total_samples}</p>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">Avg Temperature</p>
              <p className="font-medium">
                {stats.avg_temperature != null ? formatCelsius(stats.avg_temperature) : '—'}
              </p>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">Sugar Drop</p>
              <p className="font-medium">
                {stats.sugar_drop != null ? `${stats.sugar_drop.toFixed(1)} °Bx` : '—'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
