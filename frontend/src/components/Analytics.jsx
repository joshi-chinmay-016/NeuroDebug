import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity, Clock, CheckCircle2, AlertTriangle } from 'lucide-react'
import { cn } from '../lib/utils'

const analyticsData = {
  overview: {
    totalRequests: 156,
    successRate: 87,
    avgResponseTime: 1.2,
    weeklyGrowth: 23,
  },
  dailyUsage: [
    { day: 'Mon', requests: 12, success: 10 },
    { day: 'Tue', requests: 18, success: 16 },
    { day: 'Wed', requests: 24, success: 21 },
    { day: 'Thu', requests: 20, success: 18 },
    { day: 'Fri', requests: 28, success: 24 },
    { day: 'Sat', requests: 32, success: 28 },
    { day: 'Sun', requests: 22, success: 19 },
  ],
  errorTypes: [
    { type: 'TypeError', count: 45, percentage: 29 },
    { type: 'NameError', count: 38, percentage: 24 },
    { type: 'AttributeError', count: 28, percentage: 18 },
    { type: 'KeyError', count: 22, percentage: 14 },
    { type: 'ValueError', count: 15, percentage: 10 },
    { type: 'Other', count: 8, percentage: 5 },
  ],
  recentPerformance: [
    { session: 'API Auth Fix', time: '0.8s', status: 'success' },
    { session: 'Data Pipeline', time: '1.5s', status: 'success' },
    { session: 'UI Component', time: '2.1s', status: 'warning' },
    { session: 'Database Query', time: '0.6s', status: 'success' },
    { session: 'File Processing', time: '3.2s', status: 'error' },
  ],
}

export default function Analytics() {
  const maxRequests = Math.max(...analyticsData.dailyUsage.map(d => d.requests))

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground mt-2">
          Track your debugging performance and usage patterns
        </p>
      </motion.div>

      {/* Overview Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {[
          {
            label: 'Total Requests',
            value: analyticsData.overview.totalRequests,
            change: '+12%',
            icon: Activity,
            positive: true,
          },
          {
            label: 'Success Rate',
            value: `${analyticsData.overview.successRate}%`,
            change: '+5%',
            icon: CheckCircle2,
            positive: true,
          },
          {
            label: 'Avg Response Time',
            value: `${analyticsData.overview.avgResponseTime}s`,
            change: '-8%',
            icon: Clock,
            positive: true,
          },
          {
            label: 'Weekly Growth',
            value: `${analyticsData.overview.weeklyGrowth}%`,
            change: '+23%',
            icon: TrendingUp,
            positive: true,
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
              <div className={cn(
                "flex items-center text-xs font-medium",
                stat.positive ? "text-green-500" : "text-red-500"
              )}>
                {stat.positive ? (
                  <TrendingUp className="h-3 w-3 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1" />
                )}
                {stat.change}
              </div>
            </div>
            <p className="text-2xl font-bold">{stat.value}</p>
            <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Daily Usage Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-6">Daily Usage</h3>
          <div className="flex items-end gap-2 h-48">
            {analyticsData.dailyUsage.map((day, index) => (
              <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex flex-col gap-1">
                  <div
                    className="w-full bg-primary/80 rounded-t-sm transition-all hover:bg-primary"
                    style={{
                      height: `${(day.requests / maxRequests) * 100}%`,
                      minHeight: '4px',
                    }}
                  />
                  <div
                    className="w-full bg-green-500/80 rounded-b-sm transition-all hover:bg-green-500"
                    style={{
                      height: `${(day.success / maxRequests) * 100}%`,
                      minHeight: '4px',
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{day.day}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-primary/80" />
              <span>Total Requests</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500/80" />
              <span>Successful</span>
            </div>
          </div>
        </motion.div>

        {/* Error Types */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-6">Error Types Distribution</h3>
          <div className="space-y-4">
            {analyticsData.errorTypes.map((error, index) => (
              <div key={error.type} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{error.type}</span>
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
        </motion.div>

        {/* Recent Performance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="lg:col-span-2 rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-6">Recent Performance</h3>
          <div className="space-y-3">
            {analyticsData.recentPerformance.map((session, index) => (
              <div
                key={session.session}
                className="flex items-center justify-between p-4 rounded-lg bg-muted/50"
              >
                <div className="flex items-center gap-4">
                  <div
                    className={cn(
                      "p-2 rounded-lg",
                      session.status === 'success'
                        ? "bg-green-500/10"
                        : session.status === 'warning'
                        ? "bg-amber-500/10"
                        : "bg-red-500/10"
                    )}
                  >
                    {session.status === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : session.status === 'warning' ? (
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm">{session.session}</p>
                    <p className="text-xs text-muted-foreground">{session.time}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      session.status === 'success'
                        ? "text-green-500"
                        : session.status === 'warning'
                        ? "text-amber-500"
                        : "text-red-500"
                    )}
                  >
                    {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
