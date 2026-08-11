import { motion, AnimatePresence } from 'framer-motion'
import { Search, Command, LayoutDashboard, FolderKanban, Clock, Settings, User, LogOut, Plus, FileText, BarChart3 } from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()

  const commands = [
    { id: 'dashboard', label: 'Go to Dashboard', icon: LayoutDashboard, action: () => navigate('/'), category: 'Navigation' },
    { id: 'projects', label: 'Go to Projects', icon: FolderKanban, action: () => navigate('/projects'), category: 'Navigation' },
    { id: 'history', label: 'Go to History', icon: Clock, action: () => navigate('/history'), category: 'Navigation' },
    { id: 'analytics', label: 'Go to Analytics', icon: BarChart3, action: () => navigate('/analytics'), category: 'Navigation' },
    { id: 'settings', label: 'Go to Settings', icon: Settings, action: () => navigate('/settings'), category: 'Navigation' },
    { id: 'new-project', label: 'Create New Project', icon: Plus, action: () => navigate('/projects'), category: 'Actions' },
    { id: 'new-debug', label: 'Start New Debug', icon: FileText, action: () => navigate('/debug'), category: 'Actions' },
  ]

  if (isAuthenticated) {
    commands.push({ id: 'profile', label: 'Go to Profile', icon: User, action: () => navigate('/settings'), category: 'Navigation' })
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
        setSelectedIndex(prev => (prev + 1) % filteredCommands.length)
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length)
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
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.15 }}
              className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
            >
              <div className="bg-background border border-border/40 rounded-xl shadow-2xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-border/40">
                  <Search className="h-5 w-5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Type a command or search..."
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value)
                      setSelectedIndex(0)
                    }}
                    className="flex-1 bg-transparent outline-none text-sm"
                    autoFocus
                  />
                  <kbd className="px-2 py-1 text-xs bg-muted rounded">ESC</kbd>
                </div>
                <div className="max-h-96 overflow-y-auto py-2">
                  {filteredCommands.length === 0 ? (
                    <div className="px-4 py-8 text-center text-muted-foreground">
                      No commands found
                    </div>
                  ) : (
                    categories.map((category) => (
                      <div key={category} className="px-2 py-1">
                        <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          {category}
                        </div>
                        {filteredCommands
                          .filter(cmd => cmd.category === category)
                          .map((command, index) => {
                            const globalIndex = filteredCommands.indexOf(command)
                            return (
                              <motion.button
                                key={command.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.05 }}
                                onClick={() => executeCommand(command)}
                                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                                  globalIndex === selectedIndex
                                    ? 'bg-primary text-primary-foreground'
                                    : 'hover:bg-muted'
                                }`}
                              >
                                <command.icon className="h-4 w-4" />
                                <span className="flex-1 text-left">{command.label}</span>
                              </motion.button>
                            )
                          })}
                      </div>
                    ))
                  )}
                </div>
                <div className="flex items-center justify-between px-4 py-2 border-t border-border/40 text-xs text-muted-foreground">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-muted rounded">↑↓</kbd>
                      Navigate
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-muted rounded">↵</kbd>
                      Select
                    </span>
                  </div>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-muted rounded">
                      <Command className="h-3 w-3" />
                    </kbd>
                    <kbd className="px-1.5 py-0.5 bg-muted rounded">K</kbd>
                    to open
                  </span>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
