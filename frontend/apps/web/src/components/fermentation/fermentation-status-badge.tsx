"use client"

import { Badge } from '@/components/ui/badge'
import { FERMENTATION_STATUS_COLOR, FERMENTATION_STATUS_LABEL } from '@wine/ui'
import type { FermentationStatus } from '@wine/ui'

interface Props {
  status: FermentationStatus
}

export function FermentationStatusBadge({ status }: Props) {
  return (
    <Badge style={{ backgroundColor: FERMENTATION_STATUS_COLOR[status], color: '#fff' }}>
      {FERMENTATION_STATUS_LABEL[status] ?? status}
    </Badge>
  )
}
