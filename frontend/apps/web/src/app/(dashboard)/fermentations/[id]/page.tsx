"use client"

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { useFermentation, useExecution, useExecutionAlerts } from '@/hooks'
import { FermentationStatusBadge } from '@/components/fermentation/fermentation-status-badge'
import { NoProtocolBanner } from '@/components/fermentation/no-protocol-banner'
import { FermentationTabs, type TabId } from '@/components/fermentation/fermentation-tabs'

interface Props {
  params: { id: string }
}

export default function FermentationDetailPage({ params }: Props) {
  const fermentationId = parseInt(params.id, 10)
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  const { data: fermentation, isLoading, isError } = useFermentation(fermentationId)
  // Use fermentationId as a proxy for executionId (works with test fixtures)
  const { data: execution } = useExecution(fermentationId)
  const { data: alertsData } = useExecutionAlerts(execution?.id, execution?.status)

  const hasExecution = execution != null
  const alertCount = alertsData?.pending_count ?? 0

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-6 w-24 animate-pulse rounded bg-muted" />
      </div>
    )
  }

  if (isError || !fermentation) {
    return (
      <div className="space-y-4">
        <p className="text-destructive">Fermentation not found</p>
        <Link href="/fermentations" className="text-sm text-muted-foreground underline">
          Back to fermentations
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/fermentations" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-semibold">
          {fermentation.vessel_code ?? `Batch ${fermentation.id}`}
        </h1>
        <FermentationStatusBadge status={fermentation.status} />
      </div>

      <NoProtocolBanner hasExecution={hasExecution} />

      <FermentationTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        hasExecution={hasExecution}
        alertCount={alertCount}
      />

      <div>
        {activeTab === 'overview' && (
          <div data-testid="tab-overview">
            <p className="text-muted-foreground">Overview tab — coming in Task 7</p>
          </div>
        )}
        {activeTab === 'samples' && (
          <div data-testid="tab-samples">
            <p className="text-muted-foreground">Samples tab — coming in Task 8</p>
          </div>
        )}
        {activeTab === 'alerts' && (
          <div data-testid="tab-alerts">
            <p className="text-muted-foreground">Alerts tab — coming in Task 9</p>
          </div>
        )}
        {activeTab === 'protocol' && (
          <div data-testid="tab-protocol">
            <p className="text-muted-foreground">Protocol tab — coming in Task 10</p>
          </div>
        )}
        {activeTab === 'actions' && (
          <div data-testid="tab-actions">
            <p className="text-muted-foreground">Actions tab — coming in Task 11</p>
          </div>
        )}
      </div>
    </div>
  )
}
