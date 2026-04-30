"use client"

import { useFermentations } from '@/hooks'
import { KpiCard } from '@/components/dashboard/kpi-card'
import { ActiveFermentationsList } from '@/components/dashboard/active-fermentations-list'
import { Activity, AlertTriangle, CheckCircle } from 'lucide-react'

export default function DashboardPage() {
  const { data } = useFermentations()

  const items = data?.items ?? []

  const activeCount = items.filter(
    (f) => f.status === 'ACTIVE'
  ).length

  const now = new Date()
  const completedThisMonth = items.filter((f) => {
    if (f.status !== 'COMPLETED') return false
    const updated = new Date(f.updated_at)
    return updated.getMonth() === now.getMonth() && updated.getFullYear() === now.getFullYear()
  }).length

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-3 gap-4">
        <KpiCard label="Active Fermentations" value={activeCount} icon={Activity} />
        <KpiCard label="Pending Alerts" value={0} icon={AlertTriangle} />
        <KpiCard label="Completed This Month" value={completedThisMonth} icon={CheckCircle} />
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Active Fermentations</h2>
        <ActiveFermentationsList />
      </div>
    </div>
  )
}
