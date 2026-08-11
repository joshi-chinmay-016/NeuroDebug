import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity, Clock, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import analyticsService from '../services/analyticsService'
import apiClient from '../services/api'
import { cn } from '../lib/utils'

export default function Analytics() {
  const { isAuthenticated, getAccessToken } = useAuth()
  const [analyticsData, setAnalyticsData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [days, setDays] = useState(30)

  // Add auth token to API requests
  useEffect(() => {
    const token = getAccessToken()
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [isAuthenticated, getAccessToken])

  // Load analytics data
  const loadAnalytics = async () => {
    if (!isAuthenticated) return

    setIsLoading(true)
    setError('')
    try {
      const data = await analyticsService.getAnalytics(days)
      setAnalyticsData(data)
    } catch (err) {
      setError('Failed to load analytics')
      console.error('Failed to load analytics:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [isAuthenticated, days])

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className="container py-8">
        <div className="text-center py-16">
          <p className="text-muted-foreground">No analytics data available</p>
        </div>
      </div>
    )
  }

  const { usage_metrics, error_distribution, daily_stats, performance_metrics } = analyticsData
  const maxRequests = Math.max(...daily_stats.map(d => d.requests), 1)

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Track your debugging performance and usage patterns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={loadAnalytics}
            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10 px-4 py-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
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

      {/* Overview Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {[
          {
            label: 'Total Requests',
            value: usage_metrics.total_requests,
            icon: Activity,
          },
          {
            label: 'Success Rate',
            value: `${usage_metrics.success_rate}%`,
            icon: CheckCircle2,
          },
          {
            label: 'Avg Response Time',
            value: `${(usage_metrics.avg_duration_ms / 1000).toFixed(2)}s`,
            icon: Clock,
          },
          {
            label: 'Total Duration',
            value: `${(usage_metrics.total_duration_ms / 1000).toFixed(1)}s`,
            icon: TrendingUp,
          },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <stat.icon className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold">{stat.value}</p>
            <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Daily Usage Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-6">Daily Usage</h3>
          {daily_stats.length > 0 ? (
            <>
              <div className="flex items-end gap-2 h-48">
                {daily_stats.map((day, index) => {
                  const date = new Date(day.date)
                  const dayLabel = date.toLocaleDateString('en-US', { weekday: 'short' })
                  return (
                    <div key={day.date} className="flex-1 flex flex-col items-center gap-2">
                      <div
                        className="w-full bg-primary/80 rounded-t-sm transition-all hover:bg-primary"
                        style={{
                          height: `${(day.requests / maxRequests) * 100}%`,
                          minHeight: '4px',
                        }}
                      />
                      <span className="text-xs text-muted-foreground">{dayLabel}</span>
                    </div>
                  )
                })}
              </div>
              <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-primary/80" />
                  <span>Total Requests</span>
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">No daily data available</p>
          )}
        </motion.div>

        {/* Error Types */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-6">Error Types Distribution</h3>
          {error_distribution.length > 0 ? (
            <div className="space-y-4">
              {error_distribution.map((error) => (
                <div key={error.error_type} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{error.error_type}</span>
                    <span className="text-muted-foreground">{error.count} ({error.percentage}%)</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${error.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">No error data available</p>
          )}
        </motion.div>
      </div>

      {/* Performance Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
      >
        <h3 className="font-semibold mb-6">Pipeline Performance</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[
            { label: 'AST Analysis', value: performance_metrics.ast_avg_ms.toFixed(2), unit: 'ms' },
            { label: 'Rule Engine', value: performance_metrics.rule_avg_ms.toFixed(2), unit: 'ms' },
            { label: 'LLM Processing', value: performance_metrics.llm_avg_ms.toFixed(2), unit: 'ms' },
            { label: 'Patch Generation', value: performance_metrics.patch_avg_ms.toFixed(2), unit: 'ms' },
            { label: 'Verification', value: performance_metrics.verification_avg_ms.toFixed(2), unit: 'ms' },
            { label: 'Database', value: performance_metrics.database_avg_ms.toFixed(2), unit: 'ms' },
          ].map((metric, index) => (
            <div key={metric.label} className="p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className="text-xl font-bold mt-1">{metric.value} <span className="text-sm font-normal">{metric.unit}</span></p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
