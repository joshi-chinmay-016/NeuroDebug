import React from 'react'
import { Check, Loader2, X, AlertCircle } from 'lucide-react'

/**
 * 5-node Pipeline Stepper
 * 
 * Stages:
 *  1. AST Analysis
 *  2. LLM Reasoning
 *  3. Patch Validation
 *  4. Subprocess Execution
 *  5. Pytest Verification
 */
export default function PipelineStepper({
  currentStage = 0, // 0: Idle, 1: AST, 2: LLM, 3: Validate, 4: Execute, 5: Verify, 6: Completed
  isExecuting = false,
  verdict = null, // 'VERIFIED' | 'UNVERIFIED' | 'FAILED'
  compact = false,
}) {
  const stages = [
    { id: 1, label: 'AST Analysis', short: 'AST' },
    { id: 2, label: 'LLM Reasoning', short: 'LLM' },
    { id: 3, label: 'Patch Validation', short: 'Validate' },
    { id: 4, label: 'Subprocess Execution', short: 'Execute' },
    { id: 5, label: 'Pytest Verification', short: 'Verify' },
  ]

  return (
    <div className={`w-full ${compact ? 'py-2' : 'py-4'}`}>
      <div className="flex items-center justify-between relative">
        {/* Background Connecting Line */}
        <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-[1px] bg-[var(--line)] z-0" />

        {stages.map((stage, idx) => {
          const isDone = currentStage > stage.id || currentStage === 6
          const isActive = currentStage === stage.id && isExecuting
          const isFailed = currentStage === stage.id && !isExecuting && verdict === 'FAILED'

          let nodeColor = 'bg-[var(--surface-1)] border-[var(--line)] text-[var(--dim)]'
          if (isDone) {
            nodeColor = 'bg-[var(--green)]/15 border-[var(--green)] text-[var(--green)]'
          } else if (isActive) {
            nodeColor = 'bg-[var(--amber)]/20 border-[var(--amber)] text-[var(--amber)] animate-pulse'
          } else if (isFailed) {
            nodeColor = 'bg-[var(--red)]/20 border-[var(--red)] text-[var(--red)]'
          }

          return (
            <div key={stage.id} className="flex flex-col items-center relative z-10">
              <div
                className={`flex items-center justify-center rounded-full border transition-all duration-300 ${
                  compact ? 'w-6 h-6 text-[10px]' : 'w-8 h-8 text-xs'
                } ${nodeColor}`}
                title={stage.label}
              >
                {isActive ? (
                  <Loader2 className={`animate-spin ${compact ? 'w-3 h-3' : 'w-4 h-4'}`} />
                ) : isDone ? (
                  <Check className={compact ? 'w-3 h-3' : 'w-4 h-4'} />
                ) : isFailed ? (
                  <X className={compact ? 'w-3 h-3' : 'w-4 h-4'} />
                ) : (
                  <span className="font-mono">{stage.id}</span>
                )}
              </div>
              {!compact && (
                <span className="mt-1.5 font-mono text-[11px] text-[var(--dim)] font-medium">
                  {stage.short}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
