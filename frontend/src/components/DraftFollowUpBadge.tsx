import { Repeat, Send } from 'lucide-react'

interface DraftFollowUpBadgeProps {
  /** From email.trigger_type: "time_based" = follow-up, "manual" or null = initial */
  triggerType?: string | null
  /** From email.recipient_context.lead_source: "b2c" | "b2b" */
  leadSource?: string | null
  /** Optional: follow-up number (1, 2) if we had it from CRM */
  followUpCount?: number | null
  className?: string
}

export function DraftFollowUpBadge({
  triggerType,
  leadSource,
  followUpCount,
  className = '',
}: DraftFollowUpBadgeProps) {
  const isFollowUp = (triggerType || '').toLowerCase() === 'time_based'
  const isB2C = (leadSource || '').toLowerCase() === 'b2c'
  const isB2B = (leadSource || '').toLowerCase() === 'b2b'

  const followUpLabel = isFollowUp
    ? followUpCount != null && followUpCount > 0
      ? `Follow-up ${followUpCount}`
      : 'Follow-up'
    : 'Initial'

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          isFollowUp
            ? 'bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300'
            : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
        }`}
        title={isFollowUp ? 'Scheduled follow-up email' : 'First / manual'}
      >
        {isFollowUp ? (
          <Repeat className="w-3.5 h-3.5 shrink-0" aria-hidden />
        ) : (
          <Send className="w-3.5 h-3.5 shrink-0" aria-hidden />
        )}
        {followUpLabel}
      </span>
      {(isB2B || isB2C) && (
        <span
          className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
            isB2C
              ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
              : 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300'
          }`}
        >
          {isB2C ? 'B2C' : 'B2B'}
        </span>
      )}
    </div>
  )
}
