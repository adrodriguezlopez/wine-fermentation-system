"use client"

import { useState } from 'react'
import Link from 'next/link'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFermentations } from '@/hooks'
import { FermentationFiltersBar, type FermentationFilters } from '@/components/fermentation/fermentation-filters'
import { FermentationTable } from '@/components/fermentation/fermentation-table'

export default function FermentationsPage() {
  const [filters, setFilters] = useState<FermentationFilters>({ status: '', search: '' })
  const { data, isLoading } = useFermentations({ status: filters.status || undefined })

  // client-side search filter
  const fermentations = (data?.items ?? []).filter((f) => {
    if (!filters.search) return true
    const q = filters.search.toLowerCase()
    return (
      (f.vessel_code?.toLowerCase().includes(q) ?? false) ||
      f.yeast_strain.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Fermentations</h1>
        <Button asChild>
          <Link href="/fermentations/new">
            <Plus className="mr-2 h-4 w-4" />
            New Fermentation
          </Link>
        </Button>
      </div>
      <FermentationFiltersBar filters={filters} onChange={setFilters} />
      <FermentationTable fermentations={fermentations} isLoading={isLoading} />
    </div>
  )
}
