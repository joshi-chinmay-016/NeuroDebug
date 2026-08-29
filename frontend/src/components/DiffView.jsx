import React, { useState } from 'react'
import { DiffEditor } from '@monaco-editor/react'
import VerdictBadge from './VerdictBadge'
import { Copy, Check, Split, AlignJustify } from 'lucide-react'

export default function DiffView({
  originalCode = '',
  patchedCode = '',
  unifiedDiff = '',
  verdict = null,
  validationPassed = true,
  validationError = null,
}) {
  const [copied, setCopied] = useState(false)
  const [renderSideBySide, setRenderSideBySide] = useState(true)

  const handleCopy = () => {
    navigator.clipboard.writeText(patchedCode || originalCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="w-full flex flex-col h-full bg-[var(--surface-1)] border border-[var(--line)] rounded-xl overflow-hidden">
      {/* Header bar */}
      <div className="h-12 px-4 bg-[var(--surface-2)] border-b border-[var(--line)] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs uppercase tracking-wider font-semibold text-[var(--ink)]">
            Candidate Patch Diff
          </span>
          {verdict && <VerdictBadge status={verdict} size="sm" />}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setRenderSideBySide(!renderSideBySide)}
            className="p-1.5 rounded bg-[var(--surface-1)] border border-[var(--line)] text-xs text-[var(--dim)] hover:text-[var(--ink)] transition-colors flex items-center gap-1.5"
            title={renderSideBySide ? 'Switch to inline diff' : 'Switch to side-by-side diff'}
          >
            {renderSideBySide ? <Split className="w-3.5 h-3.5" /> : <AlignJustify className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline font-mono text-[10px]">
              {renderSideBySide ? 'Side-by-Side' : 'Inline'}
            </span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded bg-[var(--surface-1)] border border-[var(--line)] text-xs text-[var(--dim)] hover:text-[var(--ink)] transition-colors flex items-center gap-1.5"
            title="Copy patched code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--green)]" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline font-mono text-[10px]">
              {copied ? 'Copied' : 'Copy Fix'}
            </span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 min-h-[360px] relative">
        <DiffEditor
          height="100%"
          language="python"
          original={originalCode}
          modified={patchedCode || originalCode}
          theme="vs-dark"
          options={{
            renderSideBySide: renderSideBySide,
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            diffWordWrap: 'on',
          }}
        />
      </div>

      {/* Validation or Error footer */}
      {validationError && (
        <div className="px-4 py-2 bg-[var(--red)]/10 border-t border-[var(--red)]/30 font-mono text-xs text-[var(--red)]">
          ✕ Validation Error: {validationError}
        </div>
      )}
    </div>
  )
}
