import React, { useState, useEffect } from 'react'
import { BarChart3, Activity, CheckCircle2, AlertTriangle, XCircle, TrendingUp, Sparkles, Terminal } from 'lucide-react'
import MetricCard from './MetricCard'
import historyService from '../services/historyService'

export default function Analytics() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const todayIdx = new Date().getDay()

  // Generate last 7 days labels ending with today
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (6 - i))
    return {
      dayStr: dayNames[d.getDay()],
      dateStr: d.toDateString(),
    }
  })

  useEffect(() => {
    async function loadTelemetry() {
      try {
        setLoading(true)
        const data = await historyService.listSessions(0, 100)
        if (Array.isArray(data)) {
          setSessions(data)
        }
      } catch (err) {
        console.warn('Could not load analytics telemetry:', err)
      } finally {
        setLoading(false)
      }
    }
    loadTelemetry()
  }, [])

  // Calculate real metrics from database sessions
  const totalRuns = sessions.length
  const verifiedRuns = sessions.filter(
    (s) => s.verification_report?.verification_status === 'VERIFIED'
  ).length
  const verificationRate = totalRuns > 0 ? Math.round((verifiedRuns / totalRuns) * 100) : 0

  // Calculate real avg latency
  const durations = sessions
    .map((s) => s.pipeline_duration_ms || s.metadata?.pipeline_duration_ms || s.metadata?.total_duration_ms)
    .filter(Boolean)
  const avgLatency = durations.length > 0 ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0

  // Calculate unique error types / rules observed
  const uniqueRules = new Set(sessions.map((s) => s.error_type).filter(Boolean)).size

  // Calculate daily distribution for last 7 days
  const dailyDistribution = last7Days.map(({ dateStr, dayStr }) => {
    const daySessions = sessions.filter(
      (s) => new Date(s.created_at || Date.now()).toDateString() === dateStr
    )

    const verified = daySessions.filter(
      (s) => s.verification_report?.verification_status === 'VERIFIED'
    ).length
    const unverified = daySessions.filter(
      (s) => s.candidate_patch && s.verification_report?.verification_status !== 'VERIFIED'
    ).length
    const failed = daySessions.filter(
      (s) => !s.candidate_patch || s.verification_report?.verification_status === 'FAILED'
    ).length

    return {
      day: dayStr,
      verified,
      unverified,
      failed,
      total: daySessions.length,
    }
  })

  const maxVal = Math.max(1, ...dailyDistribution.map((d) => d.total))

  return (
    <div className="space-y-8">
      {/* Top bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
            Verification Telemetry & Analytics
          </h1>
          <p className="text-xs font-mono text-[var(--dim)] mt-1">
            Real verification metrics, deterministic rule hit rates, and execution verification ratios
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--surface-1)] border border-[var(--line)] text-xs font-mono text-[var(--dim)]">
          <Activity className="w-3.5 h-3.5 text-[var(--green)]" />
          <span>Live Database Telemetry</span>
        </div>
      </div>

      {/* Real Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-5">
        <MetricCard
          label="Total Debug Runs"
          value={totalRuns}
          icon={BarChart3}
          trend={totalRuns > 0 ? { positive: true, value: "Live session audit" } : null}
        />
        <MetricCard
          label="Verified Fixes"
          value={verifiedRuns}
          icon={CheckCircle2}
          trend={totalRuns > 0 ? { positive: true, value: `${verificationRate}% pass rate` } : null}
        />
        <MetricCard
          label="Avg Pipeline Latency"
          value={avgLatency}
          suffix="ms"
          icon={TrendingUp}
          description="Subprocess + AST execution"
        />
        <MetricCard
          label="Unique Issue Categories"
          value={uniqueRules}
          suffix="/ 13"
          icon={Activity}
          description="Deterministic rules fired"
        />
      </div>

      {/* Verification Volume Chart */}
      <div className="card-hover rounded-xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-[var(--line)] gap-4">
          <div>
            <h3 className="font-display font-bold text-sm text-[var(--ink)]">
              Daily Verification Verdict Distribution
            </h3>
            <p className="text-xs font-mono text-[var(--dim)] mt-0.5">
              Verified fixes (green) vs unverified suggestions (amber) vs execution failures (red)
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[var(--green)]" />
              <span className="text-[var(--ink)]">Verified</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[var(--amber)]" />
              <span className="text-[var(--ink)]">Unverified</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[var(--red)]" />
              <span className="text-[var(--ink)]">Failed</span>
            </span>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center font-mono text-xs text-[var(--dim)] animate-pulse">
            Loading telemetry data...
          </div>
        ) : totalRuns === 0 ? (
          <div className="h-56 flex flex-col items-center justify-center text-center p-8 bg-[var(--surface-2)]/30 rounded-xl border border-[var(--line)] space-y-2">
            <Terminal className="w-8 h-8 text-[var(--dim)] opacity-40" />
            <div className="font-display font-semibold text-sm text-[var(--ink)]">
              No Telemetry Recorded Yet
            </div>
            <p className="text-xs font-mono text-[var(--dim)] max-w-sm">
              Run your first debugging session in the Debugger to populate real execution telemetry and verdict distribution charts.
            </p>
          </div>
        ) : (
          /* Custom Real Bar Chart Visualization */
          <div className="grid grid-cols-7 gap-4 h-64 items-end pt-6">
            {dailyDistribution.map((d, idx) => {
              const vH = maxVal > 0 ? (d.verified / maxVal) * 100 : 0
              const uH = maxVal > 0 ? (d.unverified / maxVal) * 100 : 0
              const fH = maxVal > 0 ? (d.failed / maxVal) * 100 : 0

              return (
                <div key={idx} className="flex flex-col items-center gap-2 h-full justify-end group">
                  <div className="font-mono text-[10px] text-[var(--dim)] opacity-0 group-hover:opacity-100 transition-opacity">
                    {d.total} runs
                  </div>

                  {/* Stacked Vertical Bar */}
                  <div className="w-full max-w-[48px] bg-[var(--surface-2)] rounded-lg overflow-hidden flex flex-col-reverse justify-start border border-[var(--line)] h-44 relative">
                    {d.total === 0 ? (
                      <div className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-[var(--dim)] opacity-30">
                        0
                      </div>
                    ) : (
                      <>
                        <div
                          style={{ height: `${vH}%` }}
                          className="w-full bg-[var(--green)] transition-all duration-500"
                          title={`${d.verified} Verified`}
                        />
                        <div
                          style={{ height: `${uH}%` }}
                          className="w-full bg-[var(--amber)] transition-all duration-500"
                          title={`${d.unverified} Unverified`}
                        />
                        <div
                          style={{ height: `${fH}%` }}
                          className="w-full bg-[var(--red)] transition-all duration-500"
                          title={`${d.failed} Failed`}
                        />
                      </>
                    )}
                  </div>

                  <span className="text-xs font-mono text-[var(--dim)] group-hover:text-[var(--ink)] transition-colors">
                    {d.day}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
