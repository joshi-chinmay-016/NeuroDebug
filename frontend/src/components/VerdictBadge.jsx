import React from 'react'
import { CheckCircle2, AlertTriangle, XCircle, Clock } from 'lucide-react'

/**
 * Centralized Verdict Badge
 * 
 * Rules:
 *  - VERIFIED -> #3FE08A (--green)
 *  - UNVERIFIED -> #F2B84B (--amber)
 *  - VERIFICATION FAILED -> #F2555A (--red)
 *  - PENDING -> Neutral --dim
 */
export default function VerdictBadge({ status, size = 'default', showIcon = true }) {
  const norm = (status || '').toUpperCase()

  let color = 'text-[var(--dim)] border-white/10 bg-white/5'
  let label = 'PENDING'
  let Icon = Clock

  if (norm === 'VERIFIED') {
    color = 'text-[var(--green)] border-[var(--green)]/30 bg-[var(--green)]/10 shadow-sm shadow-[var(--green)]/10'
    label = 'VERIFIED'
    Icon = CheckCircle2
  } else if (norm === 'UNVERIFIED' || norm === 'CANDIDATE') {
    color = 'text-[var(--amber)] border-[var(--amber)]/30 bg-[var(--amber)]/10 shadow-sm shadow-[var(--amber)]/10'
    label = 'UNVERIFIED'
    Icon = AlertTriangle
  } else if (norm === 'FAILED' || norm === 'VERIFICATION_FAILED' || norm === 'VERIFICATION FAILED') {
    color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
    label = 'VERIFICATION FAILED'
    Icon = XCircle
  }

  const isSmall = size === 'sm'

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider rounded-md border font-semibold verdict-bounce ${
        isSmall ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs'
      } ${color}`}
    >
      {showIcon && <Icon className={isSmall ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{label}</span>
    </span>
  )
}
