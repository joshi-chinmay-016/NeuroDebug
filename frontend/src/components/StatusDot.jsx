import React from 'react'

/**
 * StatusDot
 * Ambient status indicator dot for sidebar, rows, project cards.
 */
export default function StatusDot({ status, size = 'default', pulse = false }) {
  const norm = (status || '').toUpperCase()

  let colorClass = 'bg-[var(--dim)]'
  if (norm === 'VERIFIED') colorClass = 'bg-[var(--green)]'
  else if (norm === 'UNVERIFIED' || norm === 'CANDIDATE') colorClass = 'bg-[var(--amber)]'
  else if (norm === 'FAILED' || norm === 'VERIFICATION_FAILED') colorClass = 'bg-[var(--red)]'

  const sizeClass = size === 'sm' ? 'w-1.5 h-1.5' : size === 'lg' ? 'w-2.5 h-2.5' : 'w-2 h-2'

  return (
    <span className="relative inline-flex items-center justify-center">
      {pulse && (
        <span
          className={`absolute inline-flex rounded-full opacity-75 animate-ping ${sizeClass} ${colorClass}`}
        />
      )}
      <span className={`relative inline-flex rounded-full ${sizeClass} ${colorClass}`} />
    </span>
  )
}
