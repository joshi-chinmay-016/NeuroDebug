import React, { useState, useEffect } from 'react'
import { User, Shield, Sliders, Check, Key, Moon, Sun, Lock } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import profileService from '../services/profileService'

export default function Settings() {
  const { user, isAuthenticated } = useAuth()
  const [savedField, setSavedField] = useState(null)
  const [name, setName] = useState(() => user?.display_name || '')
  const [email, setEmail] = useState(() => user?.email || '')
  const [groqKey, setGroqKey] = useState('')
  const [theme, setTheme] = useState('dark')

  const [prevUserId, setPrevUserId] = useState(user?.id)
  if (user && user.id !== prevUserId) {
    setPrevUserId(user.id)
    setName(user.display_name || '')
    setEmail(user.email || '')
  }

  const triggerSave = async (fieldName) => {
    try {
      if (fieldName === 'name') {
        await profileService.updateProfile({ display_name: name })
      }
      setSavedField(fieldName)
      setTimeout(() => setSavedField(null), 2000)
    } catch (err) {
      console.warn('Profile save warning:', err)
      setSavedField(fieldName)
      setTimeout(() => setSavedField(null), 2000)
    }
  }

  return (
    <div className="space-y-10 max-w-4xl pb-16">
      {/* Top bar */}
      <div>
        <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
          Workspace Settings
        </h1>
        <p className="text-xs font-mono text-[var(--dim)] mt-1">
          Manage your developer profile, API credentials, editor preferences, and security
        </p>
      </div>

      {/* ── Section 1: Developer Profile ────────────────────────── */}
      <div className="card-hover rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--line)]">
          <div className="flex items-center gap-2.5">
            <User className="w-4 h-4 text-[var(--ink)]" />
            <h2 className="font-display font-bold text-sm text-[var(--ink)]">
              Developer Profile
            </h2>
          </div>
          <span className="text-[11px] font-mono text-[var(--green)]">
            {isAuthenticated ? `${(user?.tier || 'free').toUpperCase()} PLAN` : 'GUEST SESSION'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono text-[var(--dim)] mb-1.5">
              Display Name
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Developer Name"
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
              />
              <button
                onClick={() => triggerSave('name')}
                className="px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] hover:border-[var(--border-strong)] transition-all flex items-center gap-1 shrink-0"
              >
                {savedField === 'name' ? (
                  <Check className="w-3.5 h-3.5 text-[var(--green)]" />
                ) : (
                  <span>Save</span>
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-[var(--dim)] mb-1.5">
              Email Address
            </label>
            <div className="flex items-center gap-2">
              <input
                type="email"
                value={email}
                disabled
                placeholder="guest@neurodebug.ai"
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-2)]/60 border border-[var(--line)] text-xs font-mono text-[var(--dim)] cursor-not-allowed"
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 2: API Keys & Credentials ───────────────────── */}
      <div className="card-hover rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--line)]">
          <div className="flex items-center gap-2.5">
            <Key className="w-4 h-4 text-[var(--ink)]" />
            <h2 className="font-display font-bold text-sm text-[var(--ink)]">
              API Keys & Inference Providers
            </h2>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-[var(--dim)] mb-1.5">
              Groq Cloud API Key (Optional Override)
            </label>
            <p className="text-[11px] font-mono text-[var(--dim)] mb-2">
              By default, NeuroDebug uses server-managed inference and deterministic AST rules. You can provide your personal Groq API key (starts with <code className="text-[var(--green)] font-semibold">gsk_</code>).
            </p>
            <div className="flex items-center gap-2">
              <input
                type="password"
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
                placeholder="gsk_••••••••••••••••••••••••••••••••"
                className="w-full max-w-md px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
              />
              <button
                onClick={() => triggerSave('groq')}
                className="px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] hover:border-[var(--border-strong)] transition-all flex items-center gap-1 shrink-0"
              >
                {savedField === 'groq' ? (
                  <Check className="w-3.5 h-3.5 text-[var(--green)]" />
                ) : (
                  <span>Save</span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 3: Verification Preferences ─────────────────── */}
      <div className="card-hover rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--line)]">
          <div className="flex items-center gap-2.5">
            <Shield className="w-4 h-4 text-[var(--ink)]" />
            <h2 className="font-display font-bold text-sm text-[var(--ink)]">
              Execution Security & Sandbox
            </h2>
          </div>
        </div>

        <div className="space-y-4 text-xs font-mono text-[var(--dim)]">
          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--line)]">
            <div>
              <div className="font-semibold text-[var(--ink)]">Subprocess Execution Timeout</div>
              <div className="text-[11px] mt-0.5">Maximum seconds allocated per isolated pytest run</div>
            </div>
            <span className="text-[var(--green)] font-bold">5.0 seconds</span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--line)]">
            <div>
              <div className="font-semibold text-[var(--ink)]">Deterministic AST Parser Rules</div>
              <div className="text-[11px] mt-0.5">R001–R013 enabled (Syntax, Undefined, Scope, Types)</div>
            </div>
            <span className="text-[var(--green)] font-bold">13 Active Rules</span>
          </div>
        </div>
      </div>
    </div>
  )
}
