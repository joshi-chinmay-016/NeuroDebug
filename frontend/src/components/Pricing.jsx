import React from 'react'
import { Check, ArrowRight, ShieldCheck, Zap } from 'lucide-react'

export default function Pricing() {
  const currentPlan = 'free' // 'guest' | 'free' | 'pro'

  const plans = [
    {
      id: 'guest',
      name: 'Guest',
      price: '$0',
      period: 'forever',
      desc: 'Instant debugging in your browser without registration.',
      limit: '1 request / day',
      features: [
        'AST static parsing',
        '13 deterministic rules',
        'Candidate patch generation',
        'Unified diff viewer',
      ],
      cta: 'Current Plan',
      isCurrent: currentPlan === 'guest',
      highlight: false,
    },
    {
      id: 'free',
      name: 'Free Account',
      price: '$0',
      period: 'forever',
      desc: 'Essential verification workspace with saved project histories.',
      limit: '5 requests / day',
      features: [
        'All Guest features',
        'Subprocess execution verification',
        'Pytest test suite runner',
        'Project workspace persistence',
        'Full session history audit trail',
      ],
      cta: 'Current Plan',
      isCurrent: currentPlan === 'free',
      highlight: true,
    },
    {
      id: 'pro',
      name: 'Pro Developer',
      price: '$19',
      period: 'per month',
      desc: 'High-throughput verification for professional teams & engineers.',
      limit: '20+ requests / day',
      features: [
        'Unlimited local deterministic runs',
        '20+ cloud LLM patches / day',
        'High-priority execution queue',
        'PostgreSQL-backed audit trail',
        'Team project sharing & export',
        'Dedicated API key support',
      ],
      cta: 'Upgrade to Pro',
      isCurrent: currentPlan === 'pro',
      highlight: false,
    },
  ]

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="text-center max-w-xl mx-auto">
        <h1 className="font-display font-bold text-3xl text-[var(--ink)] tracking-tight">
          Simple, Predictable Plans
        </h1>
        <p className="text-xs font-mono text-[var(--dim)] mt-2">
          Experience NeuroDebug immediately without login, or upgrade for higher verification throughput.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`card-hover rounded-xl p-6 flex flex-col justify-between relative ${
              plan.highlight ? 'border-l-4 border-l-[var(--green)] bg-[var(--surface-2)]/60' : ''
            }`}
          >
            <div>
              {plan.highlight && (
                <span className="font-mono text-[10px] uppercase font-bold text-[var(--green)] tracking-widest block mb-2">
                  // MOST POPULAR
                </span>
              )}

              <div className="flex items-center justify-between">
                <h3 className="font-display font-bold text-lg text-[var(--ink)]">
                  {plan.name}
                </h3>
                {plan.isCurrent && (
                  <span className="px-2 py-0.5 rounded bg-[var(--green)]/15 border border-[var(--green)]/30 text-[var(--green)] font-mono text-[10px] font-semibold">
                    ACTIVE
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="font-display text-3xl font-bold text-[var(--ink)]">
                  {plan.price}
                </span>
                <span className="text-xs font-mono text-[var(--dim)]">
                  / {plan.period}
                </span>
              </div>

              <p className="text-xs text-[var(--dim)] mt-2 leading-relaxed">
                {plan.desc}
              </p>

              <div className="mt-4 py-2 px-3 rounded bg-[var(--surface-2)] border border-[var(--line)] font-mono text-xs text-[var(--ink)] font-semibold flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-[var(--green)]" />
                <span>{plan.limit}</span>
              </div>

              <div className="mt-6 space-y-2.5">
                {plan.features.map((f, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs font-mono text-[var(--dim)]">
                    <Check className="w-3.5 h-3.5 text-[var(--green)] shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-[var(--line)]">
              {plan.isCurrent ? (
                <button
                  disabled
                  className="w-full py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] font-display font-semibold text-xs text-[var(--dim)] cursor-default"
                >
                  Current Plan
                </button>
              ) : (
                <button className="w-full py-2.5 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all flex items-center justify-center gap-2">
                  <span>{plan.cta}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
