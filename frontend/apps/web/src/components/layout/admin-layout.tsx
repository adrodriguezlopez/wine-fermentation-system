'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'

interface AdminLayoutProps {
  children: React.ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    if (user && user.role === 'WINEMAKER' && pathname.startsWith('/admin')) {
      router.replace('/403')
    }
  }, [user, pathname, router])

  if (user?.role === 'WINEMAKER' && pathname.startsWith('/admin')) {
    return null
  }

  return <>{children}</>
}
