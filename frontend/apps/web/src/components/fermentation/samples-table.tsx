"use client"
import { SAMPLE_TYPE_LABEL, formatDensity, formatCelsius } from '@wine/ui'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { SampleDto } from '@wine/shared'

function formatSampleValue(sample: SampleDto): string {
  switch (sample.sample_type) {
    case 'density': return formatDensity(sample.value)
    case 'temperature': return formatCelsius(sample.value)
    default: return `${sample.value} ${sample.units}`
  }
}

interface Props { samples: SampleDto[]; isLoading: boolean }

export function SamplesTable({ samples, isLoading }: Props) {
  if (isLoading) {
    return <div className="h-32 animate-pulse rounded-md bg-muted" />
  }
  const sorted = [...samples].sort(
    (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime()
  )
  if (sorted.length === 0) {
    return <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">No samples recorded yet</div>
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Type</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Recorded At</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((s) => (
          <TableRow key={s.id}>
            <TableCell>{SAMPLE_TYPE_LABEL[s.sample_type] ?? s.sample_type}</TableCell>
            <TableCell>{formatSampleValue(s)}</TableCell>
            <TableCell>{new Date(s.recorded_at).toLocaleString()}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
