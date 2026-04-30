"use client"

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { FERMENTATION_STATUS_COLOR, FERMENTATION_STATUS_LABEL } from '@wine/ui'
import type { FermentationDto } from '@wine/shared'

interface Props {
  fermentations: FermentationDto[]
  isLoading: boolean
}

export function FermentationTable({ fermentations, isLoading }: Props) {
  const router = useRouter()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />
        ))}
      </div>
    )
  }

  if (fermentations.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No fermentations found
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Vessel</TableHead>
          <TableHead>Vintage</TableHead>
          <TableHead>Yeast</TableHead>
          <TableHead>Mass (kg)</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Start Date</TableHead>
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {fermentations.map((f) => (
          <TableRow key={f.id}>
            <TableCell className="font-medium">{f.vessel_code ?? `Batch ${f.id}`}</TableCell>
            <TableCell>{f.vintage_year}</TableCell>
            <TableCell>{f.yeast_strain}</TableCell>
            <TableCell>{f.input_mass_kg}</TableCell>
            <TableCell>
              <Badge style={{ backgroundColor: FERMENTATION_STATUS_COLOR[f.status], color: '#fff' }}>
                {FERMENTATION_STATUS_LABEL[f.status] ?? f.status}
              </Badge>
            </TableCell>
            <TableCell>{new Date(f.start_date).toLocaleDateString()}</TableCell>
            <TableCell>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/fermentations/${f.id}`)}
              >
                View
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
