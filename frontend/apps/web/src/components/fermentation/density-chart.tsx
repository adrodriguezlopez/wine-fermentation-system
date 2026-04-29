"use client"

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import type { SampleDto } from '@wine/shared'

interface Props {
  samples: SampleDto[]
}

export function DensityChart({ samples }: Props) {
  const densitySamples = samples
    .filter((s) => s.sample_type === 'density')
    .sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime())

  if (densitySamples.length < 2) {
    return (
      <div className="flex h-48 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
        Not enough data to display chart
      </div>
    )
  }

  const data = densitySamples.map((s) => ({
    time: new Date(s.recorded_at).toLocaleDateString(),
    value: s.value,
    unit: s.units,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="time" tick={{ fontSize: 11 }} />
        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(value: number, _: string, entry: { payload: { unit: string } }) =>
            [`${value} ${entry.payload.unit}`, 'Density']
          }
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#8B1A2E"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
