import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getPriorityColor(score: string | number | null): string {
  if (!score) return 'bg-gray-500'
  const num = typeof score === 'string' ? parseInt(score) : score
  if (num >= 80) return 'bg-red-500'
  if (num >= 60) return 'bg-orange-500'
  if (num >= 40) return 'bg-yellow-500'
  return 'bg-green-500'
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'approved':
      return 'bg-green-500'
    case 'pending':
      return 'bg-yellow-500'
    case 'rejected':
      return 'bg-red-500'
    case 'sent':
      return 'bg-blue-500'
    default:
      return 'bg-gray-500'
  }
}

