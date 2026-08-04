import { useState } from 'react'

// ── Verification Badge Component ─────────────────────────────────────
function VerificationBadge({ status }) {
  const isVerified = status === 'VERIFIED'
  return (
    <span className={`verification-badge ${isVerified ? 'verified' : 'unverified'}`}>
      {isVerified ? '✓ VERIFIED' : '✕ UNVERIFIED'}
    </span>
  )
}

// ── Execution Timeline Component ───────────────────────────────────────
function ExecutionTimeline({ evidence }) {
  const { original_code_execution, patched_code_execution, test_results } = evidence

  const steps = [
    {
      name: 'Original Execution',
      status: original_code_execution.success ? 'success' : 'error',
      time: original_code_execution.execution_time,
      exitCode: original_code_execution.exit_code,
    },
    {
      name: 'Patched Execution',
      status: patched_code_execution.success ? 'success' : 'error',
      time: patched_code_execution.execution_time,
      exitCode: patched_code_execution.exit_code,
    },
  ]

  if (test_results) {
    steps.push({
      name: 'Test Execution',
      status: test_results.failed === 0 ? 'success' : 'error',
      time: test_results.duration,
      exitCode: test_results.failed > 0 ? test_results.failed : 0,
    })
  }

  return (
    <div className="execution-timeline">
      <h4 className="timeline-title">Execution Timeline</h4>
      <div className="timeline-steps">
        {steps.map((step, i) => (
          <div key={i} className={`timeline-step ${step.status}`}>
            <div className="timeline-marker" />
            <div className="timeline-content">
              <span className="timeline-step-name">{step.name}</span>
              <span className="timeline-step-time">
                {(step.time * 1000).toFixed(0)}ms
              </span>
              {step.exitCode !== undefined && (
                <span className="timeline-step-exit">
                  exit: {step.exitCode}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Expandable Logs Component ─────────────────────────────────────────
function ExpandableLogs({ title, content, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="expandable-logs" aria-expanded={isOpen}>
      <button
        className="logs-header"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className="logs-title">{title}</span>
        <span className={`logs-toggle ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      {isOpen && (
        <div className="logs-content">
          <pre className="logs-pre">{content || '(empty)'}</pre>
        </div>
      )}
    </div>
  )
}

// ── Test Summary Component ────────────────────────────────────────────
function TestSummary({ testResults }) {
  if (!testResults) return null

  const { total_tests, passed, failed, skipped, test_results: tests } = testResults

  return (
    <div className="test-summary">
      <h4 className="test-summary-title">Test Summary</h4>
      <div className="test-summary-stats">
        <div className="test-stat test-stat-total">
          <span className="stat-value">{total_tests}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="test-stat test-stat-passed">
          <span className="stat-value">{passed}</span>
          <span className="stat-label">Passed</span>
        </div>
        <div className="test-stat test-stat-failed">
          <span className="stat-value">{failed}</span>
          <span className="stat-label">Failed</span>
        </div>
        <div className="test-stat test-stat-skipped">
          <span className="stat-value">{skipped}</span>
          <span className="stat-label">Skipped</span>
        </div>
      </div>
      {tests && tests.length > 0 && (
        <div className="test-list">
          {tests.map((test, i) => (
            <div key={i} className={`test-item ${test.passed ? 'passed' : 'failed'}`}>
              <span className="test-item-icon">{test.passed ? '✓' : '✕'}</span>
              <span className="test-item-name">{test.test_name}</span>
              {test.duration > 0 && (
                <span className="test-item-time">
                  {(test.duration * 1000).toFixed(0)}ms
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Verification Panel Component ───────────────────────────────────────
export default function VerificationPanel({ verificationReport }) {
  if (!verificationReport) return null

  const {
    verification_status,
    execution_summary,
    runtime,
    failure_reason,
    evidence,
  } = verificationReport

  return (
    <div className="verification-panel">
      <div className="verification-header">
        <h3 className="verification-title">Verification Report</h3>
        <VerificationBadge status={verification_status} />
      </div>

      <div className="verification-summary">
        <div className="summary-row">
          <span className="summary-label">Status:</span>
          <span className={`summary-value ${verification_status.toLowerCase()}`}>
            {verification_status}
          </span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Runtime:</span>
          <span className="summary-value">{(runtime * 1000).toFixed(0)}ms</span>
        </div>
        {failure_reason && (
          <div className="summary-row summary-row-error">
            <span className="summary-label">Reason:</span>
            <span className="summary-value">{failure_reason}</span>
          </div>
        )}
      </div>

      <ExecutionTimeline evidence={evidence} />

      {evidence.test_results && <TestSummary testResults={evidence.test_results} />}

      <div className="verification-logs">
        <ExpandableLogs
          title="Execution Summary"
          content={execution_summary}
          defaultOpen={true}
        />
        <ExpandableLogs
          title="Original Code Output"
          content={
            evidence.original_code_execution.stdout ||
            evidence.original_code_execution.stderr
          }
        />
        <ExpandableLogs
          title="Patched Code Output"
          content={
            evidence.patched_code_execution.stdout ||
            evidence.patched_code_execution.stderr
          }
        />
        {evidence.test_results && (
          <ExpandableLogs
            title="Test Output"
            content={evidence.test_results.output}
          />
        )}
      </div>
    </div>
  )
}
