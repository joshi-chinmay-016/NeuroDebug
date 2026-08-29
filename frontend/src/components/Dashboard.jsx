import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Terminal,
  FolderGit2,
  CheckCircle2,
  ArrowRight,
  Clock,
  Sparkles,
  Plus,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react'
import MetricCard from './MetricCard'
import StatusDot from './StatusDot'
import VerdictBadge from './VerdictBadge'
import historyService from '../services/historyService'
import workspaceService from '../services/workspaceService'
import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [sessions, setSessions] = useState([])
  const [projectCount, setProjectCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true)
        const [sessionsData, projectsData] = await Promise.all([
          historyService.listSessions(0, 5).catch(() => []),
          workspaceService.listProjects(0, 100).catch(() => []),
        ])

        if (Array.isArray(sessionsData)) {
          setSessions(sessionsData)
        }
        if (Array.isArray(projectsData)) {
          setProjectCount(projectsData.length)
        }
      } catch (err) {
        console.warn('Dashboard data fetch warning:', err)
      } finally {
        setLoading(false)
      }
    }
    loadDashboardData()
  }, [])

  const verifiedCount = sessions.filter(
    (s) => s.verification_report?.verification_status === 'VERIFIED'
  ).length
  const verificationRate = sessions.length > 0 ? Math.round((verifiedCount / sessions.length) * 100) : 100

  return (
    <div className="space-y-8">
      {/* ── Top Header & Quick Actions ──────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
            Developer Overview
          </h1>
          <p className="text-xs font-mono text-[var(--dim)] mt-1">
            Real-time verification telemetry and PostgreSQL debugging history
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/debug"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all duration-150"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Start a session</span>
          </Link>
        </div>
      </div>

      {/* ── Metric Cards with Real Values ───────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <MetricCard
          label="Verification Sessions"
          value={sessions.length}
          suffix=""
          icon={Terminal}
          description="Stored in PostgreSQL"
        />
        <MetricCard
          label="Verification Success"
          value={verificationRate}
          suffix="%"
          icon={CheckCircle2}
          trend={{ positive: true, value: "Subprocess verified" }}
          description="Executed & passed tests"
        />
        <MetricCard
          label="Active Projects"
          value={projectCount}
          icon={FolderGit2}
          description="PostgreSQL workspaces"
        />
      </div>

      {/* ── Recent Activity Section ─────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[var(--dim)]" />
            <h2 className="font-display font-bold text-base text-[var(--ink)]">
              Recent Verification Runs
            </h2>
          </div>
          <Link
            to="/history"
            className="text-xs font-mono text-[var(--dim)] hover:text-[var(--ink)] flex items-center gap-1 transition-colors"
          >
            <span>View all audit logs</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center font-mono text-xs text-[var(--dim)] animate-pulse">
            Loading recent activity from PostgreSQL...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center font-mono text-xs text-[var(--dim)] bg-[var(--surface-1)] border border-[var(--line)] rounded-xl">
            No debug runs recorded yet. Start your first verification session!
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((ses) => {
              const status =
                ses.verification_report?.verification_status ||
                (ses.candidate_patch ? 'UNVERIFIED' : 'FAILED')
              return (
                <div
                  key={ses.id}
                  className="card-hover rounded-xl p-4 flex items-center justify-between gap-4 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center">
                      <Terminal className="w-4 h-4 text-[var(--ink)]" />
                    </div>
                    <div>
                      <div className="font-mono text-xs font-semibold text-[var(--ink)]">
                        {ses.error_type || 'Debug Session'}
                      </div>
                      <div className="text-[11px] font-mono text-[var(--dim)]">
                        UUID: {ses.id.slice(0, 8)}... • {new Date(ses.created_at || Date.now()).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <VerdictBadge status={status} size="sm" />
                    <Link
                      to="/history"
                      className="text-xs font-mono text-[var(--dim)] hover:text-[var(--ink)] flex items-center gap-1"
                    >
                      <span>Diff</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
