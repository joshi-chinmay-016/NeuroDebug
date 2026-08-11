import { motion } from 'framer-motion'
import { Brain, Zap, Clock, TrendingUp, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatCardSkeleton } from './Skeleton'
import { useAuth } from '../contexts/AuthContext'
import { useState, useEffect } from 'react'
import analyticsService from '../services/analyticsService'

export default function Dashboard() {
  const { isAuthenticated } = useAuth()
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState([
    {
      label: 'Total Debug Sessions',
      value: '24',
      change: '+12%',
      icon: Brain,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Success Rate',
      value: '87%',
      change: '+5%',
      icon: Zap,
      color: 'from-green-500 to-emerald-500',
    },
    {
      label: 'Avg Response Time',
      value: '1.2s',
      change: '-8%',
      icon: Clock,
      color: 'from-purple-500 to-pink-500',
    },
    {
      label: 'Weekly Growth',
      value: '23%',
      change: '+23%',
      icon: TrendingUp,
      color: 'from-orange-500 to-amber-500',
    },
  ])

  const recentActivity = [
    { id: 1, type: 'debug', message: 'Fixed TypeError in data_processor.py', time: '2 hours ago' },
    { id: 2, type: 'debug', message: 'Resolved AttributeError in auth module', time: '5 hours ago' },
    { id: 3, type: 'project', message: 'Created new project: API Integration', time: '1 day ago' },
    { id: 4, type: 'debug', message: 'Fixed KeyError in user service', time: '2 days ago' },
  ]

  useEffect(() => {
    const loadAnalytics = async () => {
      if (isAuthenticated) {
        try {
          const data = await analyticsService.getAnalytics()
          if (data) {
            setStats([
              {
                label: 'Total Debug Sessions',
                value: data.total_requests?.toString() || '0',
                change: '+12%',
                icon: Brain,
                color: 'from-blue-500 to-cyan-500',
              },
              {
                label: 'Success Rate',
                value: data.success_rate ? `${Math.round(data.success_rate * 100)}%` : '0%',
                change: '+5%',
                icon: Zap,
                color: 'from-green-500 to-emerald-500',
              },
              {
                label: 'Avg Response Time',
                value: '1.2s',
                change: '-8%',
                icon: Clock,
                color: 'from-purple-500 to-pink-500',
              },
              {
                label: 'Weekly Growth',
                value: '23%',
                change: '+23%',
                icon: TrendingUp,
                color: 'from-orange-500 to-amber-500',
              },
            ])
          }
        } catch (err) {
          console.error('Failed to load analytics:', err)
        }
      }
      setIsLoading(false)
    }
    loadAnalytics()
  }, [isAuthenticated])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
        damping: 12,
      },
    },
  }

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

      {isLoading ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8"
        >
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </motion.div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="rounded-xl border border-border/40 bg-card p-6 shadow-sm cursor-pointer"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.color}`}>
                  <stat.icon className="h-5 w-5 text-white" />
                </div>
                <span className="text-xs font-medium text-green-500">{stat.change}</span>
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Recent Activity</h2>
            <Link
              to="/history"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ x: 4 }}
                className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 cursor-pointer"
              >
                <div className="p-2 rounded-lg bg-primary/10">
                  {activity.type === 'debug' ? (
                    <Brain className="h-4 w-4 text-primary" />
                  ) : (
                    <Zap className="h-4 w-4 text-primary" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">{activity.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="rounded-xl border border-border/40 bg-card p-6 shadow-sm"
        >
          <h2 className="text-xl font-semibold mb-6">Quick Actions</h2>
          <div className="space-y-3">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Link
                to="/debug"
                className="flex items-center gap-4 p-4 rounded-lg bg-gradient-to-r from-primary to-accent text-white hover:shadow-lg hover:shadow-primary/25 transition-all"
              >
                <Brain className="h-5 w-5" />
                <div className="flex-1">
                  <p className="font-semibold">Start Debugging</p>
                  <p className="text-sm opacity-90">Debug your code with AI assistance</p>
                </div>
                <ArrowRight className="h-5 w-5" />
              </Link>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Link
                to="/projects"
                className="flex items-center gap-4 p-4 rounded-lg border border-border/40 hover:border-primary/50 hover:bg-accent/50 transition-all"
              >
                <Zap className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-semibold">Manage Projects</p>
                  <p className="text-sm text-muted-foreground">Organize your debugging sessions</p>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
              </Link>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Link
                to="/history"
                className="flex items-center gap-4 p-4 rounded-lg border border-border/40 hover:border-primary/50 hover:bg-accent/50 transition-all"
              >
                <Clock className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-semibold">View History</p>
                  <p className="text-sm text-muted-foreground">Review past debugging sessions</p>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
