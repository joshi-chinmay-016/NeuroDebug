import React, { useState, useEffect } from 'react'
import { History as HistoryIcon, Search, ArrowRight, Clock, FileCode2, Terminal, AlertCircle } from 'lucide-react'
import VerdictBadge from './VerdictBadge'
import DiffView from './DiffView'
import StatusDot from './StatusDot'
import historyService from '../services/historyService'

export default function History() {
  const [filter, setFilter] = useState('ALL') // 'ALL' | 'VERIFIED' | 'UNVERIFIED' | 'FAILED'
  const [selectedSession, setSelectedSession] = useState(null)
  const [search, setSearch] = useState('')
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true)
        const data = await historyService.listSessions(0, 50)
        if (data && Array.isArray(data)) {
          const formatted = data.map((s) => {
            const verdict = s.verification_report?.verification_status || (s.candidate_patch ? 'UNVERIFIED' : 'FAILED')
            return {
              id: s.id,
              file: `session_${s.id.slice(0, 8)}.py`,
              time: new Date(s.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              date: new Date(s.created_at || Date.now()).toLocaleDateString(),
              verdict: verdict,
              error: s.error_type || 'UnknownIssue',
              original: s.code || '',
              patched: s.candidate_patch?.patched_code || s.code || '',
              unifiedDiff: s.candidate_patch?.diff || s.candidate_patch?.unified_diff || 'No diff available',
              confidence: s.confidence_score,
            }
          })
          setSessions(formatted)
          if (formatted.length > 0) {
            setSelectedSession(formatted[0])
          }
        }
      } catch (err) {
        console.warn('Could not load PostgreSQL history sessions:', err)
      } finally {
        setLoading(false)
      }
    }
    loadHistory()
  }, [])

  const filteredItems = sessions.filter((item) => {
    const matchesFilter = filter === 'ALL' || item.verdict === filter
    const matchesSearch =
      item.file.toLowerCase().includes(search.toLowerCase()) ||
      item.error.toLowerCase().includes(search.toLowerCase()) ||
      item.original.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  return (
    <div className="space-y-8">
      {/* Top bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
            Verification History
          </h1>
          <p className="text-xs font-mono text-[var(--dim)] mt-1">
            PostgreSQL audit trail of verified patches, execution summaries, and symbolic issues
          </p>
        </div>

        {/* Verdict Filter Chips */}
        <div className="flex items-center gap-2">
          {['ALL', 'VERIFIED', 'UNVERIFIED', 'FAILED'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                filter === f
                  ? 'bg-[var(--surface-2)] text-[var(--ink)] border border-[var(--border-strong)]'
                  : 'bg-[var(--surface-1)] text-[var(--dim)] border border-[var(--line)] hover:text-[var(--ink)]'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by filename, error category, or code content..."
          className="w-full pl-9 pr-4 py-2 rounded-xl bg-[var(--surface-1)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] placeholder-[var(--dim)] focus:outline-none focus:border-[var(--border-strong)]"
        />
        <Search className="w-4 h-4 text-[var(--dim)] absolute left-3 top-2.5" />
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left List */}
        <div className="lg:col-span-5 space-y-3">
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-[var(--dim)] animate-pulse">
              Loading verification history from PostgreSQL...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 text-center font-mono text-xs text-[var(--dim)] bg-[var(--surface-1)] border border-[var(--line)] rounded-xl">
              No verification sessions found in PostgreSQL audit log.
            </div>
          ) : (
            filteredItems.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedSession(item)}
                className={`card-hover rounded-xl p-4 cursor-pointer transition-all ${
                  selectedSession?.id === item.id
                    ? 'border-[var(--border-strong)] bg-[var(--surface-2)]'
                    : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCode2 className="w-4 h-4 text-[var(--dim)]" />
                    <span className="font-mono text-xs font-semibold text-[var(--ink)]">
                      {item.file}
                    </span>
                  </div>
                  <VerdictBadge status={item.verdict} size="sm" />
                </div>

                <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-[var(--dim)]">
                  <span>{item.error}</span>
                  <span>{item.date} {item.time}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Preview */}
        <div className="lg:col-span-7 bg-[var(--surface-1)] border border-[var(--line)] rounded-xl p-6 flex flex-col min-h-[480px]">
          {selectedSession ? (
            <div className="space-y-6 flex-1 flex flex-col">
              <div className="flex items-center justify-between pb-4 border-b border-[var(--line)]">
                <div>
                  <h3 className="font-mono text-sm font-bold text-[var(--ink)]">
                    {selectedSession.file}
                  </h3>
                  <p className="text-xs font-mono text-[var(--dim)] mt-0.5">
                    Error: {selectedSession.error}
                  </p>
                </div>
                <VerdictBadge status={selectedSession.verdict} size="md" />
              </div>

              <div className="flex-1 min-h-[340px]">
                <DiffView
                  originalCode={selectedSession.original}
                  patchedCode={selectedSession.patched}
                  unifiedDiff={selectedSession.unifiedDiff}
                  verdict={selectedSession.verdict}
                  validationPassed={selectedSession.verdict === 'VERIFIED'}
                />
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[var(--dim)]">
              <HistoryIcon className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-xs font-mono">Select a session from the list to replay diff</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
