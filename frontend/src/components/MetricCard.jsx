import React, { useEffect, useState } from 'react'

/**
 * MetricCard with eased animated count-up number
 */
export default function MetricCard({ label, value, suffix = '', icon: Icon, trend = null, description = '' }) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    let start = 0
    const target = typeof value === 'number' ? value : parseFloat(value) || 0
    const duration = 600 // ms
    const frameRate = 1000 / 60
    const totalFrames = Math.round(duration / frameRate)
    let frame = 0

    const counter = setInterval(() => {
      frame++
      const progress = frame / totalFrames
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(start + (target - start) * eased)
      setDisplayValue(current)

      if (frame >= totalFrames) {
        setDisplayValue(target)
        clearInterval(counter)
      }
    }, frameRate)

    return () => clearInterval(counter)
  }, [value])

  return (
    <div className="card-hover rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wider text-[var(--dim)] font-medium">
          {label}
        </span>
        {Icon && <Icon className="w-4 h-4 text-[var(--dim)] opacity-80" />}
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="font-display text-3xl font-bold text-[var(--ink)] tracking-tight">
          {displayValue}
        </span>
        {suffix && (
          <span className="font-mono text-sm font-semibold text-[var(--dim)]">
            {suffix}
          </span>
        )}
      </div>

      {(trend || description) && (
        <div className="mt-3 flex items-center justify-between text-xs font-mono text-[var(--dim)] pt-2 border-t border-[var(--line)]">
          <span>{description}</span>
          {trend && (
            <span className={trend.positive ? 'text-[var(--green)]' : 'text-[var(--red)]'}>
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
