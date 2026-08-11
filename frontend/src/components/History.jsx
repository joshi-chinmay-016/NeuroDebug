import { motion } from 'framer-motion'
import { Search, Filter, Download, RefreshCw, Clock, ChevronDown } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import historyService from '../services/historyService'
import apiClient from '../services/api'
import { cn } from '../lib/utils'
import { TableRowSkeleton } from './Skeleton'

export default function History() {
  const { isAuthenticated, getAccessToken } = useAuth()
  const [sessions, setSessions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedProject, setSelectedProject] = useState(null)
  const [error, setError] = useState('')
  const [total, setTotal] = useState(0)

  // Add auth token to API requests
  useEffect(() => {
    const token = getAccessToken()
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [isAuthenticated, getAccessToken])

  // Load sessions
  const loadSessions = async () => {
    if (!isAuthenticated) return

    setIsLoading(true)
    setError('')
    try {
      const data = await historyService.listSessions(0, 50, selectedProject)
      setSessions(data.sessions || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError('Failed to load history')
      console.error('Failed to load history:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
  }, [isAuthenticated, selectedProject])

  const handleExport = async (sessionId, format = 'json') => {
    try {
      const data = await historyService.exportSession(sessionId, format)
      
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `debug-session-${sessionId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export session:', err)
      setError('Failed to export session')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const filteredSessions = sessions.filter((session) => {
    const matchesSearch = 
      session.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (session.error_type && session.error_type.toLowerCase().includes(searchQuery.toLowerCase()))
    return matchesSearch
  })

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Debug History</h1>
          <p className="text-muted-foreground mt-2">
            View and manage your past debugging sessions ({total} total)
          </p>
        </div>
        <button
          onClick={loadSessions}
          className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10 px-4 py-2"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-4 mb-6"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by code or error type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <div className="flex gap-2">
          <button className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors border border-border/40 bg-background hover:bg-accent h-10 px-4">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
        </div>
      </motion.div>

      {isLoading ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <TableRowSkeleton />
          <TableRowSkeleton />
          <TableRowSkeleton />
          <TableRowSkeleton />
          <TableRowSkeleton />
        </motion.div>
      ) : (
        <>
          {/* History List */}
          <div className="space-y-4">
            {filteredSessions.map((session, index) => (
              <motion.div
                key={session.session_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 + index * 0.05 }}
                className="group rounded-xl border border-border/40 bg-card p-6 shadow-sm hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Clock className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{session.error_type || 'No Error'}</h3>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatDate(session.created_at)}</span>
                        {session.pipeline_duration_ms && (
                          <>
                            <span>•</span>
                            <span>{(session.pipeline_duration_ms / 1000).toFixed(2)}s</span>
                          </>
                        )}
                        {session.confidence_score && (
                          <>
                            <span>•</span>
                            <span>{Math.round(session.confidence_score * 100)}% confidence</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleExport(session.session_id, 'json')}
                      className="p-2 rounded-md hover:bg-accent transition-colors"
                      title="Export as JSON"
                    >
                      <Download className="h-4 w-4 text-muted-foreground" />
                    </button>
                  </div>
                </div>

                <div className="rounded-lg bg-muted/50 p-4 overflow-hidden">
                  <pre className="text-sm font-mono text-muted-foreground whitespace-pre-wrap">
                    {session.code}
                  </pre>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Empty State */}
          {filteredSessions.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <Clock className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {searchQuery ? 'No matching sessions found' : 'No history found'}
              </h3>
              <p className="text-muted-foreground">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Start debugging to build your history'}
              </p>
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}
