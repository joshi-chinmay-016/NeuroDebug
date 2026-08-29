import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Search, Command, ShieldCheck, User, Sparkles, LogOut, LogIn } from 'lucide-react'
import StatusDot from './StatusDot'
import { useAuth } from '../contexts/AuthContext'

export default function Header({ usage }) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const triggerCommandPalette = () => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
  }

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <header className="h-16 px-6 bg-[var(--surface-1)] border-b border-[var(--line)] flex items-center justify-between z-20">
      {/* Search / Command Palette Trigger */}
      <div className="flex items-center gap-4">
        <button
          onClick={triggerCommandPalette}
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--dim)] hover:text-[var(--ink)] hover:border-[var(--border-strong)] transition-all duration-150"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search actions or sessions...</span>
          <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] text-[10px] text-[var(--dim)] font-mono">
            ⌘K
          </kbd>
        </button>

        {/* Ambient Engine Status */}
        <div className="hidden md:flex items-center gap-2 text-xs font-mono text-[var(--dim)] pl-3 border-l border-[var(--line)]">
          <StatusDot status="VERIFIED" />
          <span className="text-[var(--ink)] font-medium">Engine Active</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Tier & Usage pill */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono">
          <span className="text-[var(--dim)]">Usage:</span>
          <span className="text-[var(--ink)] font-semibold">
            {usage?.used || 0}/{usage?.limit || (isAuthenticated ? 5 : 1)}
          </span>
        </div>

        {/* User Account / Auth Dropdown */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-3">
            <Link
              to="/settings"
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-[var(--surface-2)] border border-transparent hover:border-[var(--line)] transition-all text-xs font-mono text-[var(--ink)]"
            >
              <div className="w-7 h-7 rounded-full bg-[var(--green)]/15 border border-[var(--green)]/30 flex items-center justify-center text-[var(--green)] font-bold text-xs uppercase">
                {user.display_name ? user.display_name.slice(0, 2) : user.email.slice(0, 2)}
              </div>
              <span className="hidden sm:inline font-semibold">
                {user.display_name || user.email.split('@')[0]}
              </span>
            </Link>

            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-[var(--dim)] hover:text-[var(--red)] hover:bg-[var(--surface-2)] transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] hover:border-[var(--border-strong)] transition-all"
          >
            <LogIn className="w-3.5 h-3.5 text-[var(--green)]" />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </header>
  )
}
