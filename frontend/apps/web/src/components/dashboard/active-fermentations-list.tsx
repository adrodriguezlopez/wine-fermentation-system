"use client"

import { useRouter } from 'next/navigation'
import { useFermentations } from '@/hooks'
import { Skeleton } from '@/components/ui/skeleton'
import { FERMENTATION_STATUS_LABEL } from '@wine/ui'

function daysActive(startDate: string): number {
  // Backend stores datetimes as UTC-naive strings (no 'Z'). Append 'Z' so
  // the browser parses them as UTC instead of local time, avoiding negative values.
  const utc = startDate.endsWith('Z') ? startDate : startDate + 'Z'
  return Math.floor((Date.now() - new Date(utc).getTime()) / (1000 * 60 * 60 * 24))
}

export function ActiveFermentationsList() {
  const router = useRouter()
  const { data, isPending, isError, dataUpdatedAt } = useFermentations({ status: 'ACTIVE' })

  const isStale = dataUpdatedAt != null && Date.now() - dataUpdatedAt > 5 * 60 * 1000
  const minutesAgo = dataUpdatedAt != null ? Math.floor((Date.now() - dataUpdatedAt) / (1000 * 60)) : 0

  if (isPending) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return <p className="text-destructive">Failed to load fermentations.</p>
  }

  const items = data?.items ?? []

  return (
    <div>
      {isStale && (
        <div className="mb-3 rounded-md bg-yellow-50 border border-yellow-200 px-4 py-2 text-sm text-yellow-800">
          Data may be stale — last updated {minutesAgo} minutes ago
        </div>
      )}
      {items.length === 0 ? (
        <p className="text-muted-foreground">No active fermentations</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="pb-2 pr-4">Vessel Code</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2 pr-4">Vintage Year</th>
              <th className="pb-2 pr-4">Input Mass (kg)</th>
              <th className="pb-2 pr-4">Start Date</th>
              <th className="pb-2">Days Active</th>
            </tr>
          </thead>
          <tbody>
            {items.map((f) => (
              <tr
                key={f.id}
                className="border-b cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => router.push(`/fermentations/${f.id}`)}
              >
                <td className="py-2 pr-4">{f.vessel_code ?? '—'}</td>
                <td className="py-2 pr-4">{FERMENTATION_STATUS_LABEL[f.status] ?? f.status}</td>
                <td className="py-2 pr-4">{f.vintage_year}</td>
                <td className="py-2 pr-4">{f.input_mass_kg}</td>
                <td className="py-2 pr-4">{new Date(f.start_date).toLocaleDateString()}</td>
                <td className="py-2">{daysActive(f.start_date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
