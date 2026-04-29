"use client"

import { AlertCircle } from 'lucide-react'

interface Props {
  hasExecution: boolean
}

export function NoProtocolBanner({ hasExecution }: Props) {
  if (hasExecution) return null
  return (
    <div className="flex items-center gap-2 rounded-md border border-yellow-300 bg-yellow-50 px-4 py-3 text-sm text-yellow-800">
      <AlertCircle className="h-4 w-4 shrink-0" />
      <span>No protocol assigned — alerts and compliance tracking unavailable.</span>
    </div>
  )
}
