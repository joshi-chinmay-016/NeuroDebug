import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Command,
  LayoutDashboard,
  FolderKanban,
  Clock,
  Settings,
  User,
  LogOut,
  Plus,
  FileText,
  BarChart3,
  CreditCard,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()

  const commands = [
    { id: 'debug', label: 'Launch Debugger', icon: FileText, action: () => navigate('/debug'), category: 'Actions' },
    { id: 'new-project', label: 'Create New Project', icon: Plus, action: () => navigate('/projects'), category: 'Actions' },
    { id: 'dashboard', label: 'Go to Dashboard', icon: LayoutDashboard, action: () => navigate('/dashboard'), category: 'Navigation' },
    { id: 'projects', label: 'Go to Projects', icon: FolderKanban, action: () => navigate('/projects'), category: 'Navigation' },
    { id: 'history', label: 'Go to History', icon: Clock, action: () => navigate('/history'), category: 'Navigation' },
    { id: 'analytics', label: 'Go to Analytics', icon: BarChart3, action: () => navigate('/analytics'), category: 'Navigation' },
    { id: 'pricing', label: 'Go to Pricing', icon: CreditCard, action: () => navigate('/pricing'), category: 'Navigation' },
    { id: 'settings', label: 'Go to Settings', icon: Settings, action: () => navigate('/settings'), category: 'Navigation' },
  ]

  if (isAuthenticated) {
    commands.push({ id: 'logout', label: 'Logout', icon: LogOut, action: () => logout(), category: 'Account' })
  }

  const filteredCommands = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  )

  const categories = [...new Set(filteredCommands.map(cmd => cmd.category))]

  const handleKeyDown = useCallback((e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setIsOpen(prev => !prev)
    }
    if (e.key === 'Escape') {
      setIsOpen(false)
    }
    if (isOpen) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % (filteredCommands.length || 1))
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + (filteredCommands.length || 1)) % (filteredCommands.length || 1))
      }
      if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].action()
        setIsOpen(false)
        setQuery('')
      }
    }
  }, [isOpen, filteredCommands, selectedIndex])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    if (isOpen) {
      setSelectedIndex(0)
      setQuery('')
    }
  }, [isOpen])

  const executeCommand = (command) => {
    command.action()
    setIsOpen(false)
    setQuery('')
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
            onClick={() => setIsOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -16 }}
            transition={{ duration: 0.15 }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50 px-4 font-display"
          >
            <div className="bg-[var(--surface-1)] border border-[var(--line)] rounded-xl shadow-2xl overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--line)] bg-[var(--surface-2)]">
                <Search className="h-4 w-4 text-[var(--dim)]" />
                <input
                  type="text"
                  placeholder="Type a command or jump to page..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-transparent text-xs font-mono text-[var(--ink)] placeholder-[var(--dim)] focus:outline-none"
                  autoFocus
                />
                <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] text-[10px] text-[var(--dim)] font-mono">
                  ESC
                </kbd>
              </div>

              <div className="max-h-72 overflow-y-auto p-2">
                {filteredCommands.length === 0 ? (
                  <div className="p-4 text-center font-mono text-xs text-[var(--dim)]">
                    No matching commands found.
                  </div>
                ) : (
                  categories.map((category) => (
                    <div key={category} className="mb-2">
                      <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-[var(--dim)] font-semibold">
                        {category}
                      </div>
                      {filteredCommands
                        .filter((cmd) => cmd.category === category)
                        .map((command) => {
                          const Icon = command.icon
                          const isSelected =
                            filteredCommands.findIndex((c) => c.id === command.id) ===
                            selectedIndex

                          return (
                            <button
                              key={command.id}
                              onClick={() => executeCommand(command)}
                              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono transition-colors text-left ${
                                isSelected
                                  ? 'bg-[var(--surface-2)] text-[var(--ink)]'
                                  : 'text-[var(--dim)] hover:text-[var(--ink)] hover:bg-[var(--surface-2)]/60'
                              }`}
                            >
                              <div className="flex items-center gap-2.5">
                                <Icon className="h-4 w-4 text-[var(--dim)]" />
                                <span>{command.label}</span>
                              </div>
                              {isSelected && (
                                <span className="text-[10px] text-[var(--green)] font-semibold">
                                  ↵ Jump
                                </span>
                              )}
                            </button>
                          )
                        })}
                    </div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
