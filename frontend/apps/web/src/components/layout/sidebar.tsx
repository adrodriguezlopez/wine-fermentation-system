'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'

interface NavItem {
  label: string
  href: string
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Fermentations', href: '/fermentations' },
  { label: 'Protocols', href: '/protocols' },
  { label: 'Vineyards', href: '/vineyards' },
  { label: 'Harvest Lots', href: '/harvest-lots' },
  { label: 'Admin — Wineries', href: '/admin/wineries', adminOnly: true },
]

export default function Sidebar() {
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)

  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || user?.role === 'ADMIN'
  )

  return (
    <aside className="flex h-full w-56 flex-col border-r bg-white">
      <div className="flex h-14 items-center border-b px-4 font-semibold text-lg">
        🍷 WineFerm
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {visibleItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'rounded-md px-3 py-2 text-sm font-medium transition-colors',
              pathname.startsWith(item.href) && item.href !== '/dashboard'
                ? 'bg-primary text-primary-foreground'
                : pathname === item.href
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
