import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * PatchView Component
 * Displays the original code, patched code, and unified diff.
 */
export default function PatchView({ patchData }) {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('patched'); // 'patched' | 'diff'

  if (!patchData) {
    return (
      <div className="result-block">
        <div className="result-block-header">patch view</div>
        <div className="result-block-body">
          <p className="empty-hint">No patch generated yet.</p>
        </div>
      </div>
    );
  }

  const { patched_code, unified_diff, validation_passed, validation_error } = patchData;

  return (
    <div className="result-block">
      <div className="result-block-header">
        patch view
        <span className={`validation-badge ${validation_passed ? 'valid' : 'invalid'}`}>
          {validation_passed ? '✓ valid' : '✕ invalid'}
        </span>
      </div>
      <div className="result-block-body" style={{ padding: 0 }}>
        {/* Tab Navigation */}
        <div className="patch-tabs">
          <button
            className={`patch-tab ${activeTab === 'patched' ? 'active' : ''}`}
            onClick={() => setActiveTab('patched')}
          >
            Patched Code
          </button>
          <button
            className={`patch-tab ${activeTab === 'diff' ? 'active' : ''}`}
            onClick={() => setActiveTab('diff')}
          >
            Unified Diff
          </button>
        </div>

        {/* Validation Error */}
        {validation_error && (
          <div className="validation-error">
            <span>⚠</span>
            <span>{validation_error}</span>
          </div>
        )}

        {/* Patched Code View */}
        {activeTab === 'patched' && (
          <div className="patch-editor-container">
            <Editor
              height="300px"
              defaultLanguage="python"
              value={patched_code}
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
              }}
            />
          </div>
        )}

        {/* Diff View */}
        {activeTab === 'diff' && (
          <div className="diff-container">
            <pre className="diff-pre">{unified_diff}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
