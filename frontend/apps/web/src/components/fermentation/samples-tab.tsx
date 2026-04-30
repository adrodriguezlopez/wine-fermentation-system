"use client"
import { useFermentationSamples } from '@/hooks'
import { SamplesTable } from './samples-table'
import { RecordSampleForm } from './record-sample-form'
import type { FermentationDto } from '@wine/shared'

interface Props { fermentation: FermentationDto }

export function SamplesTab({ fermentation }: Props) {
  const { data: samples = [], isLoading } = useFermentationSamples(fermentation.id, fermentation.status)
  return (
    <div className="space-y-6 pt-4">
      <div>
        <h3 className="mb-3 text-sm font-medium">Record New Sample</h3>
        <RecordSampleForm fermentationId={fermentation.id} />
      </div>
      <div>
        <h3 className="mb-3 text-sm font-medium">Sample History</h3>
        <SamplesTable samples={samples} isLoading={isLoading} />
      </div>
    </div>
  )
}
