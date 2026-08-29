import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Code2,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileCode2,
  Terminal,
  ShieldCheck,
  ChevronRight,
  Activity,
} from 'lucide-react'
import VerificationCore3D from './VerificationCore3D'
import VerdictBadge from './VerdictBadge'
import './LandingPageNew.css'

export default function LandingPageNew() {
  const [coreStage, setCoreStage] = useState(0) // 0: Unresolved, 1: Candidate, 2: Executing, 3: Verified
  const [navSolid, setNavSolid] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > window.innerHeight * 0.8) {
        setNavSolid(true)
      } else {
        setNavSolid(false)
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleCoreStateChange = (stage) => {
    setCoreStage(stage)
  }

  // Kicker and pill state configuration
  const stateConfig = [
    {
      kicker: '// UNVERIFIED CANDIDATE PATCH',
      label: 'UNVERIFIED',
      debugLabel: 'unresolved',
      dotColor: 'bg-[var(--red)]',
      textColor: 'text-[var(--red)]',
      badgeBorder: 'border-[var(--red)]/30',
      badgeBg: 'bg-[var(--red)]/10',
    },
    {
      kicker: '// CANDIDATE PATCH GENERATED',
      label: 'CANDIDATE',
      debugLabel: 'candidate patch',
      dotColor: 'bg-[var(--amber)]',
      textColor: 'text-[var(--amber)]',
      badgeBorder: 'border-[var(--amber)]/30',
      badgeBg: 'bg-[var(--amber)]/10',
    },
    {
      kicker: '// EXECUTING ISOLATED SUBPROCESS',
      label: 'EXECUTING',
      debugLabel: 'executing',
      dotColor: 'bg-[var(--amber)] animate-ping',
      textColor: 'text-[var(--amber)]',
      badgeBorder: 'border-[var(--amber)]/30',
      badgeBg: 'bg-[var(--amber)]/10',
    },
    {
      kicker: '// PATCH PROVEN & VERIFIED',
      label: 'VERIFIED',
      debugLabel: 'verified',
      dotColor: 'bg-[var(--green)]',
      textColor: 'text-[var(--green)]',
      badgeBorder: 'border-[var(--green)]/30',
      badgeBg: 'bg-[var(--green)]/10',
    },
  ]

  const currentConfig = stateConfig[coreStage] || stateConfig[0]

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)] font-display selection:bg-[var(--green)]/20 selection:text-[var(--green)] relative">
      {/* ── Fixed 3D Verification Core (Pinned in Viewport) ────── */}
      <div className="fixed right-0 top-0 bottom-0 w-full lg:w-[46vw] pointer-events-none z-20 hidden md:flex items-center justify-center">
        <div className="w-full max-w-[580px] h-[520px] sm:h-[580px] pointer-events-auto relative">
          <VerificationCore3D onStateChange={handleCoreStateChange} />
        </div>
      </div>

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <nav
        className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
          navSolid
            ? 'bg-[var(--surface-1)]/90 backdrop-blur-md border-b border-[var(--line)] py-3.5'
            : 'bg-transparent py-5'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center group-hover:border-[var(--border-strong)] transition-colors duration-150">
              <Activity className="w-4 h-4 text-[var(--ink)]" />
            </div>
            <span className="font-display font-bold text-lg tracking-tight text-[var(--ink)]">
              NeuroDebug
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--dim)]">
            <a href="#pipeline" className="hover:text-[var(--ink)] link-draw transition-colors">
              Pipeline
            </a>
            <a href="#verdicts" className="hover:text-[var(--ink)] link-draw transition-colors">
              Verdicts
            </a>
            <Link to="/pricing" className="hover:text-[var(--ink)] link-draw transition-colors">
              Pricing
            </Link>
            <a href="https://github.com/joshi-chinmay-016/NeuroDebug" target="_blank" rel="noreferrer" className="hover:text-[var(--ink)] link-draw transition-colors">
              Docs
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium text-[var(--dim)] hover:text-[var(--ink)] px-3.5 py-1.5 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/debug"
              className="px-4 py-2 rounded-lg text-xs font-mono font-semibold uppercase tracking-wider bg-[var(--ink)] text-[var(--bg)] hover:bg-white transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
            >
              Launch Debugger
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero Section ────────────────────────────────────────── */}
      <section className="relative min-h-screen pt-32 pb-20 flex flex-col justify-center overflow-hidden border-b border-[var(--line)] z-10">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="max-w-2xl">
            {/* Dynamic Kicker */}
            <div className="inline-flex items-center gap-2 mb-6">
              <span className={`font-mono text-xs uppercase tracking-widest font-semibold ${currentConfig.textColor}`}>
                {currentConfig.kicker}
              </span>
            </div>

            <h1 className="font-display font-bold text-4xl sm:text-6xl text-[var(--ink)] leading-[1.08] tracking-tight">
              A patch is not correct <br />
              <span className="text-[var(--dim)]">until it's proven.</span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-[var(--dim)] leading-relaxed">
              NeuroDebug couples deterministic AST static analysis with Groq neural reasoning, then validates every candidate fix through isolated subprocess execution.
            </p>

            {/* Live State Pill & Actions */}
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/debug"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-sm hover:bg-white transition-all duration-150 hover:-translate-y-0.5"
              >
                <span>Debug Code Free</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <a
                href="#pipeline"
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-lg bg-[var(--surface-1)] border border-[var(--line)] text-sm font-semibold text-[var(--ink)] hover:bg-[var(--surface-2)] hover:border-[var(--border-strong)] transition-all duration-150"
              >
                <span>Inspect Pipeline</span>
                <ChevronRight className="w-4 h-4 text-[var(--dim)]" />
              </a>

              {/* State Pill */}
              <div
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border font-mono text-xs font-semibold uppercase tracking-wider verdict-bounce ${currentConfig.badgeBorder} ${currentConfig.badgeBg}`}
              >
                <span className={`w-2 h-2 rounded-full ${currentConfig.dotColor}`} />
                <span className={currentConfig.textColor}>{currentConfig.label}</span>
              </div>
            </div>

            {/* Micro stats */}
            <div className="mt-12 pt-8 border-t border-[var(--line)] grid grid-cols-3 gap-6 max-w-lg">
              <div>
                <div className="font-mono text-xl font-bold text-[var(--ink)]">13</div>
                <div className="text-xs text-[var(--dim)] mt-0.5">Symbolic Rules</div>
              </div>
              <div>
                <div className="font-mono text-xl font-bold text-[var(--green)]">100%</div>
                <div className="text-xs text-[var(--dim)] mt-0.5">Execution Verified</div>
              </div>
              <div>
                <div className="font-mono text-xl font-bold text-[var(--ink)]">&lt; 1 ms</div>
                <div className="text-xs text-[var(--dim)] mt-0.5">AST Latency</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pipeline Section (5 Real Stages) ────────────────────── */}
      <section id="pipeline" className="py-24 border-b border-[var(--line)] bg-[var(--surface-1)]/40 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-xl">
            <div className="font-mono text-xs uppercase tracking-widest text-[var(--dim)] font-semibold">
              // ARCHITECTURE
            </div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl text-[var(--ink)] mt-2 tracking-tight">
              The Five-Stage Verification Pipeline
            </h2>
            <p className="mt-4 text-[var(--dim)] leading-relaxed">
              Every request passes through strict deterministic checks before LLM candidate generation, followed by isolated execution testing.
            </p>
          </div>

          <div className="mt-14 max-w-xl space-y-4">
            {[
              {
                step: '01',
                title: 'AST Analysis',
                desc: 'Static parse tree inspection for syntax errors and scope bindings without code execution.',
                icon: FileCode2,
              },
              {
                step: '02',
                title: 'Symbolic Rules',
                desc: '13 deterministic rules (R001–R013) catching undefined variables, mutable defaults, and antipatterns.',
                icon: ShieldCheck,
              },
              {
                step: '03',
                title: 'Candidate Patch',
                desc: 'Groq LLM generates minimal, targeted fix candidate from structured symbolic findings.',
                icon: Cpu,
              },
              {
                step: '04',
                title: 'Isolated Execution',
                desc: 'Subprocess execution in clean temporary directory with strict 30s timeout protection.',
                icon: Terminal,
              },
              {
                step: '05',
                title: 'Pytest Verify',
                desc: 'Automated test suite execution confirming fix correctness before returning final report.',
                icon: CheckCircle2,
              },
            ].map((stage) => {
              const Icon = stage.icon
              return (
                <div
                  key={stage.step}
                  className="card-hover rounded-xl p-5 flex items-start gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center shrink-0">
                    <Icon className="w-5 h-5 text-[var(--ink)]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-[var(--dim)]">
                        {stage.step}
                      </span>
                      <h3 className="font-display font-bold text-sm text-[var(--ink)]">
                        {stage.title}
                      </h3>
                    </div>
                    <p className="text-xs text-[var(--dim)] mt-1 leading-relaxed">
                      {stage.desc}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Verdicts Section (3 Real Outcomes) ──────────────────── */}
      <section id="verdicts" className="py-24 border-b border-[var(--line)] relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-xl">
            <div className="font-mono text-xs uppercase tracking-widest text-[var(--dim)] font-semibold">
              // VERDICTS
            </div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl text-[var(--ink)] mt-2 tracking-tight">
              Three Explicit Verdicts. No Hallucinations.
            </h2>
            <p className="mt-4 text-[var(--dim)] leading-relaxed">
              We never present an LLM patch as correct merely because it generated text. Every candidate is proven through real execution.
            </p>
          </div>

          <div className="mt-14 max-w-xl space-y-4">
            {/* Verified Card */}
            <div className="card-hover rounded-xl p-6 border-l-4 border-l-[var(--green)]">
              <div className="flex items-center justify-between">
                <VerdictBadge status="VERIFIED" />
                <CheckCircle2 className="w-5 h-5 text-[var(--green)]" />
              </div>
              <h3 className="font-display font-bold text-base text-[var(--ink)] mt-3">
                Verified Fix
              </h3>
              <p className="text-xs text-[var(--dim)] mt-1 leading-relaxed">
                Candidate patch applied successfully, subprocess execution succeeded, and all relevant pytest test cases passed.
              </p>
              <div className="mt-4 pt-3 border-t border-[var(--line)] font-mono text-[11px] text-[var(--green)]">
                ✓ Ready for production commit
              </div>
            </div>

            {/* Unverified Card */}
            <div className="card-hover rounded-xl p-6 border-l-4 border-l-[var(--amber)]">
              <div className="flex items-center justify-between">
                <VerdictBadge status="UNVERIFIED" />
                <AlertTriangle className="w-5 h-5 text-[var(--amber)]" />
              </div>
              <h3 className="font-display font-bold text-base text-[var(--ink)] mt-3">
                Unverified Suggestion
              </h3>
              <p className="text-xs text-[var(--dim)] mt-1 leading-relaxed">
                Patch generated but verification execution failed, timed out, or test harness was unsupported.
              </p>
              <div className="mt-4 pt-3 border-t border-[var(--line)] font-mono text-[11px] text-[var(--amber)]">
                ⚠ Manual developer inspection required
              </div>
            </div>

            {/* Verification Failed Card */}
            <div className="card-hover rounded-xl p-6 border-l-4 border-l-[var(--red)]">
              <div className="flex items-center justify-between">
                <VerdictBadge status="FAILED" />
                <XCircle className="w-5 h-5 text-[var(--red)]" />
              </div>
              <h3 className="font-display font-bold text-base text-[var(--ink)] mt-3">
                Verification Failed
              </h3>
              <p className="text-xs text-[var(--dim)] mt-1 leading-relaxed">
                Patch execution threw runtime errors, failed unit assertions, or introduced a functional regression.
              </p>
              <div className="mt-4 pt-3 border-t border-[var(--line)] font-mono text-[11px] text-[var(--red)]">
                ✕ Patch rejected automatically
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Quiet Footer ────────────────────────────────────────── */}
      <footer className="py-12 bg-[var(--bg)] font-mono text-xs text-[var(--dim)] border-t border-[var(--line)] relative z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="font-bold text-[var(--ink)] font-display text-sm">NeuroDebug</span>
            <span>—</span>
            <span>Neuro-Symbolic AI Debugger & Verification Engine</span>
          </div>

          <div className="flex items-center gap-6">
            <Link to="/debug" className="hover:text-[var(--ink)] link-draw">Debugger</Link>
            <Link to="/pricing" className="hover:text-[var(--ink)] link-draw">Pricing</Link>
            <a href="https://github.com/joshi-chinmay-016/NeuroDebug" target="_blank" rel="noreferrer" className="hover:text-[var(--ink)] link-draw">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
