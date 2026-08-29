import React, { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation, Link } from 'react-router-dom'
import {
  Activity,
  Terminal,
  Award,
  FolderGit2,
  History as HistoryIcon,
  BarChart3,
  CreditCard,
  Settings as SettingsIcon,
  ChevronLeft,
  ChevronRight,
  Command,
} from 'lucide-react'
import StatusDot from './StatusDot'
import Header from './Header'
import { useAuth } from '../contexts/AuthContext'
import historyService from '../services/historyService'

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, isAuthenticated } = useAuth()
  const [usage, setUsage] = useState({
    used: 0,
    limit: isAuthenticated ? 5 : 1,
    tier: isAuthenticated ? (user?.tier || 'free') : 'guest',
  })
  const location = useLocation()

  useEffect(() => {
    async function checkDailyUsage() {
      const tier = isAuthenticated ? (user?.tier || 'free') : 'guest'
      const limit = tier === 'pro' ? 20 : (tier === 'free' ? 5 : 1)

      try {
        const sessions = await historyService.listSessions(0, 100)
        if (Array.isArray(sessions)) {
          // Count sessions from today
          const today = new Date().toDateString()
          const todaySessions = sessions.filter((s) => new Date(s.created_at || Date.now()).toDateString() === today)
          setUsage({ used: todaySessions.length, limit, tier })
          return
        }
      } catch (err) {
        // Fallback
      }
      setUsage((prev) => ({ ...prev, limit, tier }))
    }

    checkDailyUsage()
  }, [isAuthenticated, user])

  // Dashboard starts first
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Activity },
    { path: '/debug', label: 'Debugger', icon: Terminal },
    { path: '/evaluation', label: 'Evaluation', icon: Award },
    { path: '/projects', label: 'Projects', icon: FolderGit2 },
    { path: '/history', label: 'History', icon: HistoryIcon },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    { path: '/pricing', label: 'Pricing', icon: CreditCard },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  const usagePercent = Math.min(100, Math.round((usage.used / usage.limit) * 100))

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)] flex font-display selection:bg-[var(--green)]/20 selection:text-[var(--green)]">
      {/* ── Left Sidebar (Collapsible) ─────────────────────────── */}
      <aside
        className={`bg-[var(--surface-1)] border-r border-[var(--line)] flex flex-col justify-between transition-all duration-300 z-30 ${
          collapsed ? 'w-16' : 'w-60'
        }`}
      >
        <div>
          {/* Logo & Toggle */}
          <div className="h-16 px-4 flex items-center justify-between border-b border-[var(--line)]">
            <Link to="/" className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center shrink-0">
                <Activity className="w-4 h-4 text-[var(--ink)]" />
              </div>
              {!collapsed && (
                <span className="font-display font-bold text-sm text-[var(--ink)] whitespace-nowrap">
                  NeuroDebug
                </span>
              )}
            </Link>

            <button
              onClick={() => setCollapsed(!collapsed)}
              className="w-7 h-7 rounded-md bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center text-[var(--dim)] hover:text-[var(--ink)] transition-colors"
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Navigation Links (Dashboard First) */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-mono font-medium transition-all duration-150 relative group ${
                    isActive
                      ? 'bg-[var(--surface-2)] text-[var(--ink)] shadow-sm'
                      : 'text-[var(--dim)] hover:text-[var(--ink)] hover:bg-[var(--surface-2)]/60'
                  }`}
                >
                  {/* Left Accent Bar on Active */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[2.5px] h-4 bg-[var(--green)] rounded-r" />
                  )}

                  <Icon className="w-4 h-4 shrink-0" />
                  {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* Sidebar Footer: Usage Bar */}
        <div className="p-4 border-t border-[var(--line)]">
          {!collapsed ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] font-mono text-[var(--dim)]">
                <span>Usage Today</span>
                <span className="text-[var(--ink)] font-semibold">
                  {usage.used} / {usage.limit}
                </span>
              </div>
              <div className="h-1.5 w-full bg-[var(--surface-2)] rounded-full overflow-hidden border border-[var(--line)]">
                <div
                  className="h-full bg-[var(--green)] transition-all duration-500 ease-out"
                  style={{ width: `${usagePercent}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-[var(--dim)] pt-1">
                <span className="capitalize">{usage.tier} Tier</span>
                <Link to="/pricing" className="text-[var(--green)] hover:underline">
                  Upgrade
                </Link>
              </div>
            </div>
          ) : (
            <div className="flex justify-center" title={`${usage.used}/${usage.limit} requests today`}>
              <StatusDot status="VERIFIED" />
            </div>
          )}
        </div>
      </aside>

      {/* ── Main Content Area ───────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        <Header usage={usage} />
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto page-enter">
          <Outlet context={{ usage, setUsage }} />
        </main>
      </div>
    </div>
  )
}
