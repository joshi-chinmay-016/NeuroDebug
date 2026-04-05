import { useState, useCallback, useEffect, useRef } from 'react'
import axios from 'axios'
import Editor from '@monaco-editor/react'

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

const LS_KEY = 'neurodebug_openai_key'
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
    try { localStorage.removeItem(LS_KEY) } catch (_) {}
    inputRef.current?.focus()
  }

  const isSet = apiKey && apiKey.trim().startsWith('sk-')

  return (
    <div className="key-bar">
      <label htmlFor="openai-key-input" className="key-label">
        OpenAI key
      </label>
      <div className="key-input-wrap">
        <input
          ref={inputRef}
          id="openai-key-input"
          type={visible ? 'text' : 'password'}
          className="key-input"
          placeholder="sk-..."
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
        {isSet ? '✓ set' : 'not set — AI explanation will be skipped'}
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

// ── App ───────────────────────────────────────────────────────────
export default function App() {
  const [code, setCode]         = useState(SAMPLES[0].code)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')

  // Load saved key from localStorage on mount
  const [apiKey, setApiKey] = useState(() => {
    try { return localStorage.getItem(LS_KEY) || '' } catch (_) { return '' }
  })

  useEffect(() => {
    axios.get(`${API}/health`, { timeout: 4000 })
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  const handleDebug = useCallback(async () => {
    if (!code.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
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

  const onKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleDebug()
    }
  }

  return (
    <div className="app" onKeyDown={onKeyDown}>

      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <a href="/" className="logo">
            <div className="logo-mark" aria-hidden="true">⬡</div>
            <span className="logo-name">NeuroDebug</span>
          </a>
          <div className="header-right">
            <div className="api-status" title="Backend API">
              <span className={`status-dot ${apiStatus}`} />
              <span>api {apiStatus}</span>
            </div>
            <span className="header-tag">v1.0</span>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="main">
        <div className="page-heading">
          <h1>Python Code Debugger</h1>
          <p>
            Paste code below and hit <strong>Run analysis</strong>.
            Uses static AST rules and GPT-4 to explain what's wrong.{' '}
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs →</a>
          </p>
        </div>

        {/* ── API key bar — above the workspace ── */}
        <ApiKeyBar apiKey={apiKey} setApiKey={setApiKey} />

        <div className="workspace">

          {/* ── Left: editor ── */}
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
                theme="vs-dark"
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

          {/* ── Right: output ── */}
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
                <span className={`error-badge ${badgeClass(result.error_type)}`}>
                  {result.error_type}
                </span>
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

      {/* ── Footer ── */}
      <footer className="footer">
        <span>NeuroDebug — static analysis + GPT-4 explanations</span>
        <div className="footer-links">
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">api docs</a>
          <a href="https://github.com" target="_blank" rel="noreferrer">github</a>
        </div>
      </footer>
    </div>
  )
}
