
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default function RootPage() {
  const cookieStore = cookies()
  const hasSession = Boolean(
    cookieStore.get('wine_access_token') || cookieStore.get('wine_refresh_token')
  )

  redirect(hasSession ? '/dashboard' : '/login')
}
