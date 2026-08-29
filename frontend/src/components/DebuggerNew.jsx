import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import {
  Play,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Terminal,
  ShieldCheck,
  Cpu,
  FileCode2,
  BookOpen,
  Zap,
  ArrowRight,
  X,
  Lock,
} from 'lucide-react'
import VerdictBadge from './VerdictBadge'
import DiffView from './DiffView'
import Skeleton from './Skeleton'
import apiClient from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const SAMPLES = [
  {
    name: 'Mutable Default',
    category: 'R005',
    code: `def append_item(val, items=[]):
    # Bug: Mutable default argument retains state across calls
    items.append(val)
    return items

print("Call 1:", append_item(1))
print("Call 2:", append_item(2))
`,
  },
  {
    name: 'Undefined Variable',
    category: 'R002',
    code: `def calculate_circle_area(radius):
    # Bug: Typo in variable name 'radiux'
    pi = 3.14159
    area = pi * (radiux ** 2)
    return area

print("Area:", calculate_circle_area(5))
`,
  },
  {
    name: 'Division by Zero',
    category: 'R006',
    code: `def compute_rate(total, count):
    # Bug: Zero division when count is 0
    return total / count

print("Rate:", compute_rate(100, 0))
`,
  },
  {
    name: 'Bare Except',
    category: 'R004',
    code: `def parse_data(raw_text):
    # Bug: Bare except suppresses all errors indiscriminately
    try:
        return int(raw_text)
    except:
        return None

print("Parsed:", parse_data("invalid"))
`,
  },
  {
    name: 'Return Outside Func',
    category: 'R003',
    code: `# Bug: Module-level return statement outside function
threshold = 10
if threshold > 5:
    return threshold * 2
`,
  },
]

export default function DebuggerNew() {
  const { user, isAuthenticated } = useAuth()
  const [code, setCode] = useState(SAMPLES[0].code)
  const [isRunning, setIsRunning] = useState(false)
  const [response, setResponse] = useState(null)
  const [activeTab, setActiveTab] = useState('diff') // 'diff' | 'evidence' | 'issues'
  const [errorMsg, setErrorMsg] = useState(null)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [quotaInfo, setQuotaInfo] = useState(null)

  const handleRunDebug = async () => {
    if (!code.trim()) return

    setIsRunning(true)
    setErrorMsg(null)

    try {
      const res = await apiClient.post('/debug', { code: code })
      setResponse(res.data)
    } catch (err) {
      console.error('Debug API Error:', err)
      const detail = err.response?.data?.detail || err.message

      // Check if limit exceeded (HTTP 429)
      if (
        err.response?.status === 429 ||
        (typeof detail === 'object' && detail?.error === 'usage_limit_exceeded') ||
        (typeof detail === 'string' && detail.includes('limit exceeded'))
      ) {
        setQuotaInfo(typeof detail === 'object' ? detail : { message: detail })
        setShowUpgradeModal(true)
      } else {
        setErrorMsg(typeof detail === 'string' ? detail : detail?.message || 'Verification failed')
      }
    } finally {
      setIsRunning(false)
    }
  }

  const handleReset = () => {
    setCode('')
    setResponse(null)
    setErrorMsg(null)
  }

  const loadSample = (sample) => {
    setCode(sample.code)
    setResponse(null)
    setErrorMsg(null)
  }

  const verdictStatus =
    response?.verification_report?.verification_status ||
    (response?.candidate_patch ? 'UNVERIFIED' : null)

  return (
    <div className="w-full h-full flex flex-col space-y-6 relative">
      {/* ── Top Control Bar ──────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-[var(--surface-1)] border border-[var(--line)] rounded-xl">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center">
            <Terminal className="w-4 h-4 text-[var(--ink)]" />
          </div>
          <div>
            <h1 className="font-display font-bold text-sm text-[var(--ink)]">
              Verification Workspace
            </h1>
            <p className="text-xs font-mono text-[var(--dim)]">
              Interactive deterministic analyzer & Groq LLM verification engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            disabled={isRunning}
            className="px-3.5 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--dim)] hover:text-[var(--ink)] hover:border-[var(--border-strong)] transition-all flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>

          <button
            onClick={handleRunDebug}
            disabled={isRunning || !code.trim()}
            className="px-5 py-2 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all duration-150 hover:-translate-y-0.5 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-2 shadow-sm"
          >
            {isRunning ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-[var(--bg)] border-t-transparent rounded-full animate-spin" />
                <span>Verifying Subprocess...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Verify & Debug</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Sample Test Cases Toolbar ─────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-[var(--surface-1)] border border-[var(--line)] rounded-xl">
        <div className="flex items-center gap-1.5 px-2 text-xs font-mono text-[var(--dim)] font-semibold">
          <BookOpen className="w-3.5 h-3.5 text-[var(--green)]" />
          <span>Sample Bug Snippets:</span>
        </div>
        {SAMPLES.map((sample) => (
          <button
            key={sample.name}
            onClick={() => loadSample(sample)}
            className="px-3 py-1.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-2)]/80 transition-all flex items-center gap-1.5"
          >
            <span className="text-[10px] text-[var(--dim)]">{sample.category}</span>
            <span>{sample.name}</span>
          </button>
        ))}
      </div>

      {/* ── Main Split Workspace ──────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[520px]">
        {/* Left Column: Monaco Code Editor */}
        <div className="lg:col-span-6 flex flex-col bg-[var(--surface-1)] border border-[var(--line)] rounded-xl overflow-hidden min-h-[460px]">
          <div className="h-12 px-4 bg-[var(--surface-2)] border-b border-[var(--line)] flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--dim)]">
              <FileCode2 className="w-4 h-4" />
              <span className="font-semibold text-[var(--ink)]">snippet.py</span>
            </div>
            <span className="font-mono text-[11px] text-[var(--dim)]">Python 3.11</span>
          </div>

          <div className="flex-1 relative">
            <Editor
              height="100%"
              defaultLanguage="python"
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                fontSize: 13,
                fontFamily: "'JetBrains Mono', monospace",
                lineNumbers: 'on',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 12 },
              }}
            />

            {/* Empty state placeholder prompt */}
            {!code && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-6 text-center">
                <div className="font-mono text-xs text-[var(--dim)]">
                  // Paste your buggy Python code or select a sample snippet above
                  <span className="inline-block w-1.5 h-3 bg-[var(--green)] ml-1.5 animate-pulse" />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Findings, Diff & Verification Evidence */}
        <div className="lg:col-span-6 flex flex-col bg-[var(--surface-1)] border border-[var(--line)] rounded-xl overflow-hidden min-h-[460px]">
          {/* Tabs bar */}
          <div className="h-12 px-4 bg-[var(--surface-2)] border-b border-[var(--line)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('diff')}
                className={`px-3 py-1.5 rounded-md font-mono text-xs transition-colors ${
                  activeTab === 'diff'
                    ? 'bg-[var(--surface-1)] text-[var(--ink)] font-semibold border border-[var(--line)]'
                    : 'text-[var(--dim)] hover:text-[var(--ink)]'
                }`}
              >
                Candidate Diff
              </button>

              <button
                onClick={() => setActiveTab('evidence')}
                className={`px-3 py-1.5 rounded-md font-mono text-xs transition-colors ${
                  activeTab === 'evidence'
                    ? 'bg-[var(--surface-1)] text-[var(--ink)] font-semibold border border-[var(--line)]'
                    : 'text-[var(--dim)] hover:text-[var(--ink)]'
                }`}
              >
                Verification Evidence
              </button>

              <button
                onClick={() => setActiveTab('issues')}
                className={`px-3 py-1.5 rounded-md font-mono text-xs transition-colors ${
                  activeTab === 'issues'
                    ? 'bg-[var(--surface-1)] text-[var(--ink)] font-semibold border border-[var(--line)]'
                    : 'text-[var(--dim)] hover:text-[var(--ink)]'
                }`}
              >
                Issues ({response?.detected_issues?.length || 0})
              </button>
            </div>

            {verdictStatus && <VerdictBadge status={verdictStatus} size="sm" />}
          </div>

          {/* Panel Body */}
          <div className="flex-1 p-5 overflow-y-auto">
            {isRunning ? (
              <div className="space-y-4 py-6">
                <div className="font-mono text-xs text-[var(--amber)] flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[var(--amber)] animate-ping" />
                  <span>Executing verification subprocess pass...</span>
                </div>
                <div className="space-y-3">
                  <div className="h-4 bg-[var(--surface-2)] rounded w-3/4 animate-pulse" />
                  <div className="h-4 bg-[var(--surface-2)] rounded w-1/2 animate-pulse" />
                  <div className="h-28 bg-[var(--surface-2)] rounded w-full animate-pulse mt-4" />
                </div>
              </div>
            ) : errorMsg ? (
              <div className="p-4 rounded-lg bg-[var(--red)]/10 border border-[var(--red)]/30 font-mono text-xs text-[var(--red)]">
                ✕ Error: {typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg)}
              </div>
            ) : response ? (
              <>
                {/* Diff Tab */}
                {activeTab === 'diff' && (
                  <div className="h-full flex flex-col space-y-4">
                    {response.explanation && (
                      <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] font-mono text-xs">
                        <div className="font-bold text-[var(--dim)] uppercase text-[10px] tracking-wider mb-1 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-[var(--green)]" />
                          <span>Analysis & Reasoning:</span>
                        </div>
                        <p className="text-[var(--ink)] whitespace-pre-wrap leading-relaxed">
                          {response.explanation}
                        </p>
                      </div>
                    )}

                    {response.candidate_patch ? (
                      <div className="flex-1 min-h-[320px]">
                        <DiffView
                          originalCode={response.candidate_patch.original_code}
                          patchedCode={response.candidate_patch.patched_code}
                          unifiedDiff={response.candidate_patch.unified_diff}
                          verdict={verdictStatus}
                          validationPassed={response.candidate_patch.validation_passed}
                        />
                      </div>
                    ) : (
                      <div className="text-center py-12 font-mono text-xs text-[var(--dim)]">
                        No candidate patch generated for clean code.
                      </div>
                    )}
                  </div>
                )}

                {/* Evidence Tab */}
                {activeTab === 'evidence' && (
                  <div className="space-y-4 text-xs font-mono">
                    <div className="p-4 rounded-lg bg-[var(--surface-2)] border border-[var(--line)]">
                      <div className="font-semibold text-[var(--ink)] mb-2">
                        Execution Summary:
                      </div>
                      <pre className="text-[var(--dim)] whitespace-pre-wrap">
                        {response.verification_report?.execution_summary ||
                          'No execution evidence available.'}
                      </pre>
                    </div>

                    {response.verification_report?.evidence && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--line)]">
                          <div className="text-[var(--dim)]">Original Subprocess:</div>
                          <div
                            className={`mt-1 font-semibold ${
                              response.verification_report.evidence.original_code_execution.success
                                ? 'text-[var(--green)]'
                                : 'text-[var(--red)]'
                            }`}
                          >
                            {response.verification_report.evidence.original_code_execution.success
                              ? '✓ Passed'
                              : '✕ Failed'}
                          </div>
                        </div>

                        <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--line)]">
                          <div className="text-[var(--dim)]">Patched Subprocess:</div>
                          <div
                            className={`mt-1 font-semibold ${
                              response.verification_report.evidence.patched_code_execution.success
                                ? 'text-[var(--green)]'
                                : 'text-[var(--red)]'
                            }`}
                          >
                            {response.verification_report.evidence.patched_code_execution.success
                              ? '✓ Passed'
                              : '✕ Failed'}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Issues Tab */}
                {activeTab === 'issues' && (
                  <div className="space-y-3">
                    {response.detected_issues?.length > 0 ? (
                      response.detected_issues.map((issue, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[var(--ink)]">
                              {issue.rule_id}: {issue.category}
                            </span>
                            <span className="text-[var(--dim)]">Line {issue.line || 'N/A'}</span>
                          </div>
                          <p className="mt-1 text-[var(--dim)]">{issue.message}</p>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-12 font-mono text-xs text-[var(--green)]">
                        ✓ No symbolic issues detected.
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8">
                <div className="w-12 h-12 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center text-[var(--dim)] mb-4">
                  <Terminal className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-sm text-[var(--ink)]">
                  Ready to verify code
                </h3>
                <p className="text-xs text-[var(--dim)] max-w-sm mt-1">
                  Click "Verify & Debug" or select one of the sample snippets above to run AST analysis, patch generation, and pytest execution.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── High-Conversion Pro Upgrade Modal ────────────────────── */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm page-enter">
          <div className="w-full max-w-md bg-[var(--surface-1)] border border-[var(--line)] rounded-2xl p-6 shadow-2xl relative space-y-6">
            <button
              onClick={() => setShowUpgradeModal(false)}
              className="absolute top-4 right-4 text-[var(--dim)] hover:text-[var(--ink)] p-1 rounded-lg hover:bg-[var(--surface-2)] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--green)]/15 border border-[var(--green)]/30 flex items-center justify-center">
                <Zap className="w-5 h-5 text-[var(--green)]" />
              </div>
              <div>
                <h3 className="font-display font-bold text-base text-[var(--ink)]">
                  Daily Quota Exceeded
                </h3>
                <p className="text-xs font-mono text-[var(--dim)] mt-0.5">
                  You've used all verifications for today
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between text-[var(--dim)]">
                <span>Current Plan:</span>
                <span className="font-bold uppercase text-[var(--ink)]">
                  {isAuthenticated ? (user?.tier || 'Free') : 'Guest'}
                </span>
              </div>
              <div className="flex items-center justify-between text-[var(--dim)]">
                <span>Daily Limit:</span>
                <span className="font-bold text-[var(--red)]">
                  {quotaInfo?.current_usage || (isAuthenticated ? 5 : 1)} / {quotaInfo?.limit || (isAuthenticated ? 5 : 1)} Used
                </span>
              </div>
            </div>

            <div className="space-y-2.5">
              <div className="text-xs font-mono text-[var(--dim)] font-semibold">
                Upgrade to Pro Developer Plan:
              </div>
              <ul className="space-y-2 text-xs font-mono text-[var(--ink)]">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--green)]" />
                  <span>20+ Cloud LLM Verifications / day</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--green)]" />
                  <span>Multi-file workspaces & audit replay</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--green)]" />
                  <span>Pytest isolated test execution runner</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--green)]" />
                  <span>High-priority execution queue</span>
                </li>
              </ul>
            </div>

            <div className="space-y-2 pt-2">
              <Link
                to="/pricing"
                className="w-full py-3 rounded-xl bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all flex items-center justify-center gap-2 shadow-lg"
              >
                <span>Upgrade to Pro — $19/mo</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              {!isAuthenticated && (
                <Link
                  to="/register"
                  className="w-full py-2.5 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] text-[var(--ink)] font-mono text-xs hover:border-[var(--border-strong)] transition-all flex items-center justify-center gap-2 text-center block"
                >
                  <span>Or Create Free Account (5/day)</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
