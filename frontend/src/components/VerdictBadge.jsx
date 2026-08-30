import React from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  HelpCircle,
  AlertOctagon,
  AlertCircle,
  ShieldAlert,
} from 'lucide-react'

/**
 * Standardized 9-State Verdict Badge
 * 
 * Explicit Verification States:
 *  - VERIFIED -> #3FE08A (--green)
 *  - UNVERIFIED -> #F2B84B (--amber)
 *  - FAILED_VERIFICATION -> #F2555A (--red)
 *  - NO_FIX_FOUND -> Neutral --dim
 *  - INVALID_PATCH -> #F2555A (--red)
 *  - EXECUTION_TIMEOUT -> #FFA500 (--amber)
 *  - TEST_FAILURE -> #F2555A (--red)
 *  - EXECUTION_ERROR -> #F2555A (--red)
 *  - VERIFICATION_UNAVAILABLE -> Neutral --dim
 */
export default function VerdictBadge({ status, size = 'default', showIcon = true }) {
  const norm = (status || '').toUpperCase()

  let color = 'text-[var(--dim)] border-white/10 bg-white/5'
  let label = 'PENDING'
  let Icon = Clock

  switch (norm) {
    case 'VERIFIED':
      color = 'text-[var(--green)] border-[var(--green)]/30 bg-[var(--green)]/10 shadow-sm shadow-[var(--green)]/10'
      label = 'VERIFIED'
      Icon = CheckCircle2
      break

    case 'UNVERIFIED':
    case 'CANDIDATE':
      color = 'text-[var(--amber)] border-[var(--amber)]/30 bg-[var(--amber)]/10 shadow-sm shadow-[var(--amber)]/10'
      label = 'UNVERIFIED'
      Icon = AlertTriangle
      break

    case 'FAILED_VERIFICATION':
    case 'FAILED':
    case 'VERIFICATION_FAILED':
    case 'VERIFICATION FAILED':
      color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
      label = 'FAILED VERIFICATION'
      Icon = XCircle
      break

    case 'TEST_FAILURE':
      color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
      label = 'TEST FAILURE'
      Icon = XCircle
      break

    case 'INVALID_PATCH':
      color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
      label = 'INVALID PATCH'
      Icon = AlertOctagon
      break

    case 'EXECUTION_TIMEOUT':
    case 'TIMEOUT':
      color = 'text-amber-400 border-amber-500/30 bg-amber-500/10 shadow-sm shadow-amber-500/10'
      label = 'TIMEOUT'
      Icon = Clock
      break

    case 'EXECUTION_ERROR':
    case 'ERROR':
      color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
      label = 'EXECUTION ERROR'
      Icon = AlertCircle
      break

    case 'NO_FIX_FOUND':
      color = 'text-[var(--dim)] border-white/10 bg-white/5'
      label = 'NO FIX FOUND'
      Icon = HelpCircle
      break

    case 'SANDBOX_ERROR':
      color = 'text-[var(--red)] border-[var(--red)]/30 bg-[var(--red)]/10 shadow-sm shadow-[var(--red)]/10'
      label = 'SANDBOX ERROR'
      Icon = ShieldAlert
      break

    case 'NOT_VERIFIABLE':
      color = 'text-[var(--amber)] border-[var(--amber)]/30 bg-[var(--amber)]/10 shadow-sm shadow-[var(--amber)]/10'
      label = 'NOT VERIFIABLE'
      Icon = HelpCircle
      break

    case 'NOT_RUN':
      color = 'text-[var(--dim)] border-white/10 bg-white/5'
      label = 'NOT RUN'
      Icon = Clock
      break

    case 'VERIFICATION_UNAVAILABLE':
      color = 'text-[var(--dim)] border-white/10 bg-white/5'
      label = 'VERIFICATION UNAVAILABLE'
      Icon = ShieldAlert
      break

    default:
      color = 'text-[var(--dim)] border-white/10 bg-white/5'
      label = norm || 'PENDING'
      Icon = Clock
      break
  }

  const isSmall = size === 'sm'

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider rounded-md border font-semibold verdict-bounce transition-colors duration-150 ${
        isSmall ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs'
      } ${color}`}
      title={`State Machine Status: ${norm}`}
    >
      {showIcon && <Icon className={isSmall ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{label}</span>
    </span>
  )
}
