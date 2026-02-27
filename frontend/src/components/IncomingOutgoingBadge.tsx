import { ArrowDownLeft, ArrowUpRight } from 'lucide-react'

interface IncomingOutgoingBadgeProps {
  emailType?: string | null
  /** Compact: icon only with title for screen readers */
  compact?: boolean
  className?: string
}

export function IncomingOutgoingBadge({ emailType, compact, className = '' }: IncomingOutgoingBadgeProps) {
  const isOutgoing = (emailType || '').toLowerCase() === 'outbound'
  const label = isOutgoing ? 'Outgoing' : 'Incoming'

  if (compact) {
    return (
      <span
        title={label}
        className={`inline-flex items-center justify-center rounded p-0.5 ${isOutgoing ? 'text-blue-600 bg-blue-100' : 'text-emerald-600 bg-emerald-100'} ${className}`}
        aria-label={label}
      >
        {isOutgoing ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownLeft className="w-4 h-4" />}
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${isOutgoing ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'} ${className}`}
    >
      {isOutgoing ? (
        <>
          <ArrowUpRight className="w-3.5 h-3.5" aria-hidden />
          Outgoing
        </>
      ) : (
        <>
          <ArrowDownLeft className="w-3.5 h-3.5" aria-hidden />
          Incoming
        </>
      )}
    </span>
  )
}
