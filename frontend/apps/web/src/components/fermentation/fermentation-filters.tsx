"use client"

import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export interface FermentationFilters {
  status: string   // '' = all
  search: string
}

interface Props {
  filters: FermentationFilters
  onChange: (filters: FermentationFilters) => void
}

export function FermentationFiltersBar({ filters, onChange }: Props) {
  const [localSearch, setLocalSearch] = useState(filters.search)

  // debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange({ ...filters, search: localSearch })
    }, 300)
    return () => clearTimeout(timer)
  }, [localSearch])

  return (
    <div className="flex gap-3">
      <Select
        value={filters.status}
        onValueChange={(value) => onChange({ ...filters, status: value === '__all__' ? '' : value })}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All</SelectItem>
          <SelectItem value="ACTIVE">Active</SelectItem>
          <SelectItem value="LAG">Lag</SelectItem>
          <SelectItem value="SLOW">Slow</SelectItem>
          <SelectItem value="STUCK">Stuck</SelectItem>
          <SelectItem value="DECLINE">Decline</SelectItem>
          <SelectItem value="COMPLETED">Completed</SelectItem>
        </SelectContent>
      </Select>
      <Input
        placeholder="Search by vessel or yeast..."
        value={localSearch}
        onChange={(e) => setLocalSearch(e.target.value)}
        className="max-w-sm"
      />
    </div>
  )
}
