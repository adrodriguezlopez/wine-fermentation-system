"use client"

import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

export type TabId = 'overview' | 'samples' | 'alerts' | 'protocol' | 'actions'

const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'samples', label: 'Samples' },
  { id: 'alerts', label: 'Alerts' },
  { id: 'protocol', label: 'Protocol' },
  { id: 'actions', label: 'Actions' },
]

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  hasExecution: boolean
  alertCount: number
}

export function FermentationTabs({ activeTab, onTabChange, hasExecution, alertCount }: Props) {
  return (
    <div className="flex gap-1 border-b">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            'relative flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-colors',
            activeTab === tab.id
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          {tab.label}
          {tab.id === 'alerts' && hasExecution && alertCount > 0 && (
            <Badge className="h-4 min-w-4 px-1 text-xs" style={{ backgroundColor: '#DC2626', color: '#fff' }}>
              {alertCount}
            </Badge>
          )}
        </button>
      ))}
    </div>
  )
}
