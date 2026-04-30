import { useState, useCallback, useEffect, useRef } from 'react'
import axios from 'axios'
import Editor from '@monaco-editor/react'
import BlurText from './components/BlurText'
import SplashCursor from './components/SplashCursor'
import ThemeToggle from './components/ThemeToggle'
import { useTheme } from './components/ThemeProvider'

// ── Sample snippets ───────────────────────────────────────────────
const SAMPLES = [
  {
    label: 'undefined var',
    code: `def greet(name):
    message = "Hello, " + nam  # 'nam' is not defined
    return message

result = greet("Alice")
print(result)`,
  },
  {
    label: 'syntax error',
    code: `def check_age(age):
    if age >= 18
        return "Adult"
    else:
        return "Minor"`,
  },
  {
    label: 'div by zero',
    code: `def calculate(x):
    result = x / 0
    return result

print(calculate(10))`,
  },
  {
    label: 'mutable default',
    code: `def append_item(item, lst=[]):
    lst.append(item)
    return lst

print(append_item(1))
print(append_item(2))`,
  },
  {
    label: 'bare except',
    code: `def read_file(path):
    try:
        with open(path) as f:
            return f.read()
    except:
        pass

data = read_file("config.json")
print(data)`,
  },
  {
    label: 'clean code',
    code: `def fibonacci(n: int) -> list[int]:
    """Return a list of the first n Fibonacci numbers."""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    sequence = [0, 1]
    for _ in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]

if __name__ == "__main__":
    print(fibonacci(10))`,
  },
]

const LS_KEY = 'neurodebug_groq_key'
const LEGACY_LS_KEY = 'neurodebug_openai_key'
const HISTORY_KEY = 'neurodebug_saved_outputs'
const API    = import.meta.env.VITE_API_URL || ''

// ── API call — sends user key in body ─────────────────────────────
async function runDebug(code, apiKey) {
  const body = { code }
  if (apiKey && apiKey.trim()) body.api_key = apiKey.trim()
  const res = await axios.post(`${API}/debug`, body, { timeout: 30000 })
  return res.data
}

// ── Badge helpers ─────────────────────────────────────────────────
function badgeClass(errorType) {
  if (!errorType || errorType === 'Clean') return 'badge-clean'
  const t = errorType.toLowerCase()
  if (t.includes('syntax') || t.includes('zero') || t.includes('error')) return 'badge-error'
  if (t.includes('warn') || t.includes('loop') || t.includes('default') || t.includes('except'))
    return 'badge-warning'
  return 'badge-info'
}

function issueIcon(sev) {
  if (sev === 'error')   return '✕'
  if (sev === 'warning') return '△'
  return 'i'
}

// ── Copy button ───────────────────────────────────────────────────
function safeHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
    return Array.isArray(saved) ? saved : []
  } catch (_) {
    return []
  }
}

function formatSavedOutput(item) {
  const issues = item.result.symbolic_issues?.length
    ? item.result.symbolic_issues
        .map((issue) => `- [${issue.severity}] ${issue.rule_id}: ${issue.message}`)
        .join('\n')
    : '- No symbolic issues reported.'

  return `# NeuroDebug Analysis

Saved: ${new Date(item.savedAt).toLocaleString()}
Error type: ${item.result.error_type}
Confidence: ${Math.round(item.result.confidence_score * 100)}%

## Code
\`\`\`python
${item.code}
\`\`\`

## Explanation
${item.result.explanation}

## Suggested Fix
${item.result.suggested_fix || 'No suggested fix returned.'}

## Symbolic Issues
${issues}
`
}

function downloadSavedOutput(item) {
  const blob = new Blob([formatSavedOutput(item)], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const stamp = new Date(item.savedAt).toISOString().replace(/[:.]/g, '-')

  link.href = url
  link.download = `neurodebug-analysis-${stamp}.md`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function CopyBtn({ text, className = 'copy-btn-sm' }) {
  const [did, setDid] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setDid(true)
    setTimeout(() => setDid(false), 1800)
  }
  return (
    <button className={className} onClick={copy} id="copy-fix-btn">
      {did ? 'copied!' : 'copy'}
    </button>
  )
}

// ── Key input field ───────────────────────────────────────────────
function ApiKeyBar({ apiKey, setApiKey }) {
  const [visible, setVisible] = useState(false)
  const inputRef = useRef(null)

  const handleChange = (e) => {
    const val = e.target.value
    setApiKey(val)
    try { localStorage.setItem(LS_KEY, val) } catch (_) {}
  }

  const handleClear = () => {
    setApiKey('')
    try {
      localStorage.removeItem(LS_KEY)
      localStorage.removeItem(LEGACY_LS_KEY)
    } catch (_) {}
    inputRef.current?.focus()
  }

  const isSet = apiKey && apiKey.trim().startsWith('gsk_')

  return (
    <div className="key-bar">
      <label htmlFor="groq-key-input" className="key-label">
        Groq key
      </label>
      <div className="key-input-wrap">
        <input
          ref={inputRef}
          id="groq-key-input"
          type={visible ? 'text' : 'password'}
          className="key-input"
          placeholder="gsk_..."
          value={apiKey}
          onChange={handleChange}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          className="key-toggle"
          onClick={() => setVisible(v => !v)}
          type="button"
          tabIndex={-1}
          title={visible ? 'Hide key' : 'Show key'}
        >
          {visible ? '🙈' : '👁'}
        </button>
        {apiKey && (
          <button
            className="key-clear"
            onClick={handleClear}
            type="button"
            title="Clear key"
          >
            ×
          </button>
        )}
      </div>
      <span className={`key-status ${isSet ? 'key-ok' : 'key-missing'}`}>
        {isSet ? 'set' : 'not set - AI explanation will be skipped'}
      </span>
    </div>
  )
}

// ── Results ───────────────────────────────────────────────────────
function Results({ data }) {
  const pct    = Math.round(data.confidence_score * 100)
  const bClass = badgeClass(data.error_type)

  return (
    <>
      <div className="result-block">
        <div className="result-block-header">
          diagnosis
          <span className={`error-badge ${bClass}`}>{data.error_type}</span>
        </div>
        <div className="result-block-body">
          <div className="confidence">
            <span className="confidence-label">confidence</span>
            <div className="conf-track">
              <div className="conf-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="conf-pct">{pct}%</span>
          </div>
        </div>
      </div>

      <div className="result-block">
        <div className="result-block-header">explanation</div>
        <div className="result-block-body">
          <p className="explanation">{data.explanation}</p>
        </div>
      </div>

      {data.suggested_fix && data.suggested_fix !== 'Code appears correct.' && (
        <div className="result-block">
          <div className="result-block-header">suggested fix</div>
          <div className="result-block-body" style={{ padding: 0 }}>
            <div className="fix-wrap">
              <pre className="fix-pre">{data.suggested_fix}</pre>
              <CopyBtn text={data.suggested_fix} />
            </div>
          </div>
        </div>
      )}

      {data.symbolic_issues?.length > 0 && (
        <div className="result-block">
          <div className="result-block-header">
            static analysis
            <span style={{ fontWeight: 400, color: 'var(--text-3)' }}>
              {data.symbolic_issues.length} issue{data.symbolic_issues.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="result-block-body" style={{ padding: '0 1rem' }}>
            <div className="issues-list">
              {data.symbolic_issues.map((iss, i) => (
                <div key={i} className="issue-row">
                  <span
                    className="issue-icon"
                    style={{
                      color: iss.severity === 'error'   ? 'var(--red)'
                           : iss.severity === 'warning' ? 'var(--amber)'
                           : 'var(--blue)',
                    }}
                  >
                    {issueIcon(iss.severity)}
                  </span>
                  <span className="issue-msg">{iss.message}</span>
                  <span className="issue-rule">{iss.rule_id}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// ── Landing Page Component ─────────────────────────────────────────
function HistorySection({ history, onDownload }) {
  return (
    <section className="history-section" id="history">
      <div className="history-header">
        <div>
          <p className="history-kicker">History</p>
          <h2>Saved outputs</h2>
        </div>
        <span className="history-count">{history.length}</span>
      </div>

      {history.length === 0 ? (
        <p className="history-empty">Saved analysis outputs will appear here.</p>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <article className="history-item" key={item.id}>
              <div className="history-item-main">
                <span className={`error-badge ${badgeClass(item.result.error_type)}`}>
                  {item.result.error_type}
                </span>
                <p className="history-summary">{item.result.explanation}</p>
                <span className="history-date">{new Date(item.savedAt).toLocaleString()}</span>
              </div>
              <button type="button" className="btn btn-ghost history-download" onClick={() => onDownload(item)}>
                download
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function LandingPage({ onEnter }) {
  const aboutSectionRef = useRef(null)

  const handleAnimationComplete = () => {
    console.log('Animation completed!')
  }

  const scrollToAbout = () => {
    aboutSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="landing-container">
      <SplashCursor 
        DENSITY_DISSIPATION={3}
        VELOCITY_DISSIPATION={5}
        PRESSURE={0.4}
        CURL={33}
        COLOR="#44ef58"
      />

      <div className="landing-nav">
        <button type="button" className="landing-nav-link" onClick={scrollToAbout}>
          About
        </button>
        <ThemeToggle />
        <button type="button" className="landing-cta-btn" onClick={onEnter}>
          Debug your code
        </button>
      </div>
      
      <section className="hero-section">
        <div className="hero-text-container" onClick={onEnter}>
          <BlurText
            text="Neuro-Debug"
            delay={140}
            animateBy="letters"
            direction="bottom"
            onAnimationComplete={handleAnimationComplete}
            className="hero-text mb-8"
          />
        </div>
        
        <div className="scroll-indicator">
          <div className="scroll-dot" />
        </div>
      </section>

      <section ref={aboutSectionRef} className="developer-card-section">
        <div className="developer-card">
          <p className="developer-eyebrow">Meet the developer</p>
          <span className="developer-name">Chinmay Joshi</span>
          <span className="developer-role">FullStack Developer</span>
          
          <div className="future-content-placeholder">
            {/* Space for future texts */}
          </div>
        </div>
      </section>
    </div>
  )
}

// ── Dashboard Component ───────────────────────────────────────────
function Dashboard({ 
  code, setCode, 
  result, setResult, 
  loading, setLoading, 
  error, setError, 
  apiStatus, setApiStatus,
  apiKey, setApiKey,
  history,
  historyOpen,
  saveStatus,
  onToggleHistory,
  onSaveResult,
  onDownloadHistoryItem,
  handleDebug
}) {
  const { isDark } = useTheme()

  const onKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleDebug()
    }
  }

  return (
    <div className="app" onKeyDown={onKeyDown}>
      <header className="header">
        <div className="header-inner">
          <a href="/" className="logo">
            <div className="logo-mark" aria-hidden="true">⬡</div>
            <span className="logo-name">NeuroDebug</span>
          </a>
          <div className="header-right">
            <button type="button" className="history-nav-btn" onClick={onToggleHistory}>
              History
              <span>{history.length}</span>
            </button>
            <ThemeToggle />
            <div className="api-status" title="Backend API">
              <span className={`status-dot ${apiStatus}`} />
              <span>api {apiStatus}</span>
            </div>
            <span className="header-tag">v1.0</span>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="page-heading">
          <h1>Python Code Debugger</h1>
          <p>
            Paste code below and hit <strong>Run analysis</strong>.
            Uses static AST rules and Groq to explain what's wrong.{' '}
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs →</a>
          </p>
        </div>

        <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

        {historyOpen && (
          <HistorySection history={history} onDownload={onDownloadHistoryItem} />
        )}

        <div className="workspace">
          <div className="panel">
            <div className="panel-titlebar">
              <div className="panel-titlebar-left">
                <div className="win-dots" aria-hidden="true">
                  <span className="win-dot" />
                  <span className="win-dot" />
                  <span className="win-dot" />
                </div>
                <span className="file-tab">untitled.py</span>
              </div>
              <span className="char-count">{code.length} chars</span>
            </div>

            <div className="editor-wrap">
              <Editor
                height="420px"
                defaultLanguage="python"
                value={code}
                onChange={(v) => setCode(v || '')}
                theme={isDark ? 'vs-dark' : 'light'}
                options={{
                  fontSize: 13,
                  fontFamily: "'JetBrains Mono', monospace",
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  lineNumbers: 'on',
                  renderLineHighlight: 'line',
                  tabSize: 4,
                  automaticLayout: true,
                  padding: { top: 14, bottom: 14 },
                  overviewRulerLanes: 0,
                  renderLineHighlightOnlyWhenFocus: true,
                }}
                loading={
                  <div className="spinner-wrap">
                    <div className="spinner" />
                    <span>loading editor…</span>
                  </div>
                }
              />
            </div>

            <div className="toolbar">
              <div className="toolbar-left">
                <button
                  id="debug-btn"
                  className="btn btn-primary"
                  onClick={handleDebug}
                  disabled={loading || !code.trim()}
                >
                  {loading ? (
                    <>
                      <div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} />
                      analysing…
                    </>
                  ) : (
                    'Run analysis'
                  )}
                </button>
              </div>
              <div className="toolbar-right">
                <span className="shortcut-hint">ctrl+enter</span>
                <button
                  id="clear-btn"
                  className="btn btn-ghost"
                  onClick={() => { setCode(''); setResult(null); setError(null) }}
                >
                  clear
                </button>
              </div>
            </div>

            <div className="samples-bar">
              <p className="samples-label">try a sample:</p>
              <div className="samples-row">
                {SAMPLES.map((s) => (
                  <button
                    key={s.label}
                    id={`sample-${s.label.replace(/\s+/g, '-')}`}
                    className="sample-btn"
                    onClick={() => {
                      setCode(s.code)
                      setResult(null)
                      setError(null)
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="panel" role="region" aria-label="Analysis output">
            <div className="panel-titlebar">
              <div className="panel-titlebar-left">
                <div className="win-dots" aria-hidden="true">
                  <span className="win-dot" />
                  <span className="win-dot" />
                  <span className="win-dot" />
                </div>
                <span className="panel-label">output</span>
              </div>
              {result && (
                <div className="output-actions">
                  <button type="button" className="save-output-btn" onClick={onSaveResult}>
                    {saveStatus || 'save output'}
                  </button>
                  <span className={`error-badge ${badgeClass(result.error_type)}`}>
                    {result.error_type}
                  </span>
                </div>
              )}
            </div>

            <div className="output-body">
              {loading && (
                <div className="spinner-wrap" role="status">
                  <div className="spinner" />
                  <span>running analysis…</span>
                </div>
              )}

              {!loading && error && (
                <div className="error-banner" role="alert">
                  <span>⚠</span>
                  <span>{error}</span>
                </div>
              )}

              {!loading && result && <Results data={result} />}

              {!loading && !result && !error && (
                <div className="empty-state">
                  <div className="empty-arrow">↑</div>
                  <p className="empty-hint">
                    results will appear here after you click "Run analysis"
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <span>NeuroDebug - static analysis + Groq explanations</span>
        <div className="footer-links">
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">api docs</a>
          <a href="https://github.com" target="_blank" rel="noreferrer">github</a>
        </div>
      </footer>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────
export default function App() {
  const [showApp, setShowApp]   = useState(false)
  const [code, setCode]         = useState(SAMPLES[0].code)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')
  const [history, setHistory] = useState(safeHistory)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [saveStatus, setSaveStatus] = useState('')

  const [apiKey, setApiKey] = useState(() => {
    try {
      const storedGroqKey = localStorage.getItem(LS_KEY)
      if (storedGroqKey) return storedGroqKey

      const legacyKey = localStorage.getItem(LEGACY_LS_KEY)
      if (legacyKey?.startsWith('gsk_')) {
        localStorage.setItem(LS_KEY, legacyKey)
        return legacyKey
      }

      return ''
    } catch (_) {
      return ''
    }
  })

  useEffect(() => {
    axios.get(`${API}/health`, { timeout: 4000 })
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
    } catch (_) {}
  }, [history])

  const handleDebug = useCallback(async () => {
    if (!code.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    setSaveStatus('')
    try {
      const data = await runDebug(code, apiKey)
      setResult(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Could not reach the backend.'
      )
    } finally {
      setLoading(false)
    }
  }, [code, apiKey, loading])

  const handleSaveResult = useCallback(() => {
    if (!result) return

    const item = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      savedAt: new Date().toISOString(),
      code,
      result,
    }

    setHistory((current) => [item, ...current].slice(0, 20))
    setHistoryOpen(true)
    setSaveStatus('saved')
    downloadSavedOutput(item)
    setTimeout(() => setSaveStatus(''), 1800)
  }, [code, result])

  const handleDownloadHistoryItem = useCallback((item) => {
    downloadSavedOutput(item)
  }, [])

  if (!showApp) {
    return <LandingPage onEnter={() => setShowApp(true)} />
  }

  return (
    <Dashboard 
      code={code} setCode={setCode}
      result={result} setResult={setResult}
      loading={loading} setLoading={setLoading}
      error={error} setError={setError}
      apiStatus={apiStatus} setApiStatus={setApiStatus}
      apiKey={apiKey} setApiKey={setApiKey}
      history={history}
      historyOpen={historyOpen}
      saveStatus={saveStatus}
      onToggleHistory={() => setHistoryOpen(open => !open)}
      onSaveResult={handleSaveResult}
      onDownloadHistoryItem={handleDownloadHistoryItem}
      handleDebug={handleDebug}
    />
  )
}
