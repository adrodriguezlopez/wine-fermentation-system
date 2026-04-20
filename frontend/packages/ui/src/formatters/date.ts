import { formatDistanceToNow, format } from 'date-fns'

export function formatRelative(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return formatDistanceToNow(d, { addSuffix: true })
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, HH:mm')
}

/** Use for historical data where the year is ambiguous without context. */
export function formatDateTimeWithYear(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d yyyy, HH:mm')
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, yyyy')
}

export function formatDurationHours(hours: number): string {
  const days = Math.floor(hours / 24)
  const remaining = Math.floor(hours % 24)
  if (days === 0) return `${remaining}h`
  if (remaining === 0) return `${days} day${days > 1 ? 's' : ''}`
  return `${days} day${days > 1 ? 's' : ''} ${remaining}h`
}

