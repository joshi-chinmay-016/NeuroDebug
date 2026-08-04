import Editor from '@monaco-editor/react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * DiffView Component
 * Displays side-by-side diff using Monaco Diff Editor.
 */
export default function DiffView({ originalCode, modifiedCode }) {
  const { theme } = useTheme();

  if (!originalCode || !modifiedCode) {
    return (
      <div className="result-block">
        <div className="result-block-header">diff view</div>
        <div className="result-block-body">
          <p className="empty-hint">No code to compare.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="result-block">
      <div className="result-block-header">side-by-side diff</div>
      <div className="result-block-body" style={{ padding: 0 }}>
        <div className="diff-editor-container">
          <Editor
            height="400px"
            defaultLanguage="python"
            value={modifiedCode}
            originalValue={originalCode}
            theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
            options={{
              readOnly: true,
              fontSize: 13,
              fontFamily: "'JetBrains Mono', monospace",
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              renderLineHighlight: 'line',
              tabSize: 4,
              automaticLayout: true,
              padding: { top: 14, bottom: 14 },
              diffWordWrap: 'on',
              renderSideBySide: true,
              enableSplitViewResizing: true,
              renderOverviewRuler: true,
            }}
            // Use diff mode
            modification={originalCode !== modifiedCode ? 'diff' : undefined}
          />
        </div>
      </div>
    </div>
  );
}
