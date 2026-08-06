// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion'
import { Brain, Zap, Clock, TrendingUp, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '../lib/utils'

const stats = [
  {
    name: 'Total Debug Sessions',
    value: '24',
    change: '+12%',
    icon: Brain,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  {
    name: 'Successful Fixes',
    value: '18',
    change: '+8%',
    icon: CheckCircle2,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
  {
    name: 'Avg. Response Time',
    value: '1.2s',
    change: '-15%',
    icon: Clock,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  {
    name: 'Remaining Requests',
    value: '3/5',
    change: 'Free Plan',
    icon: Zap,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
  },
]

const recentActivity = [
  {
    id: 1,
    type: 'debug',
    message: 'Fixed undefined variable error',
    time: '2 minutes ago',
    status: 'success',
  },
  {
    id: 2,
    type: 'debug',
    message: 'Analyzed syntax error in function',
    time: '15 minutes ago',
    status: 'success',
  },
  {
    id: 3,
    type: 'warning',
    message: 'Usage limit approaching',
    time: '1 hour ago',
    status: 'warning',
  },
  {
    id: 4,
    type: 'debug',
    message: 'Attempted division by zero fix',
    time: '2 hours ago',
    status: 'error',
  },
]

const quickActions = [
  {
    name: 'New Debug Session',
    description: 'Start debugging your code',
    href: '/debug',
    icon: Brain,
  },
  {
    name: 'View Projects',
    description: 'Manage your debugging projects',
    href: '/projects',
    icon: TrendingUp,
  },
  {
    name: 'View History',
    description: 'Check past debug sessions',
    href: '/history',
    icon: Clock,
  },
  {
    name: 'Upgrade Plan',
    description: 'Get more requests and features',
    href: '/pricing',
    icon: Zap,
  },
]

export default function Dashboard() {
  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome back! Here's an overview of your debugging activity.
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                <p className="text-2xl font-bold mt-2">{stat.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>
              </div>
              <div className={cn("p-3 rounded-lg", stat.bgColor)}>
                <stat.icon className={cn("h-5 w-5", stat.color)} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="lg:col-span-1"
        >
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            {quickActions.map((action) => (
              <Link
                key={action.name}
                to={action.href}
                className="flex items-center gap-4 p-4 rounded-lg border border-border/40 bg-card hover:bg-accent/50 transition-colors group"
              >
                <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <action.icon className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">{action.name}</p>
                  <p className="text-xs text-muted-foreground">{action.description}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="lg:col-span-2"
        >
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <div className="rounded-xl border border-border/40 bg-card shadow-sm">
            <div className="divide-y divide-border/40">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center gap-4 p-4 hover:bg-accent/50 transition-colors"
                >
                  <div
                    className={cn(
                      "p-2 rounded-lg",
                      activity.status === 'success'
                        ? "bg-green-500/10"
                        : activity.status === 'warning'
                        ? "bg-amber-500/10"
                        : "bg-red-500/10"
                    )}
                  >
                    {activity.status === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : activity.status === 'warning' ? (
                      <AlertCircle className="h-4 w-4 text-amber-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.message}</p>
                    <p className="text-xs text-muted-foreground">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Upgrade Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="mt-8 rounded-xl border border-border/40 bg-gradient-to-r from-primary/10 to-accent/10 p-6"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Upgrade to Pro</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Get 20+ daily requests, priority processing, and advanced features.
            </p>
          </div>
          <Link
            to="/pricing"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
          >
            View Plans
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
