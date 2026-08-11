import { createContext, useContext, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import { cn } from '../lib/utils'

const NotificationContext = createContext(null)

export const useNotification = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider')
  }
  return context
}

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([])

  const addNotification = useCallback((notification) => {
    const id = Date.now()
    setNotifications((prev) => [...prev, { ...notification, id }])
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const success = useCallback((message, title = 'Success') => {
    addNotification({ type: 'success', title, message })
  }, [addNotification])

  const error = useCallback((message, title = 'Error') => {
    addNotification({ type: 'error', title, message })
  }, [addNotification])

  const info = useCallback((message, title = 'Info') => {
    addNotification({ type: 'info', title, message })
  }, [addNotification])

  const warning = useCallback((message, title = 'Warning') => {
    addNotification({ type: 'warning', title, message })
  }, [addNotification])

  const value = {
    notifications,
    addNotification,
    removeNotification,
    success,
    error,
    info,
    warning,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer notifications={notifications} onRemove={removeNotification} />
    </NotificationContext.Provider>
  )
}

const NotificationContainer = ({ notifications, onRemove }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onRemove={() => onRemove(notification.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

const NotificationItem = ({ notification, onRemove }) => {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertCircle,
  }

  const colors = {
    success: 'bg-green-500/10 border-green-500/20 text-green-500',
    error: 'bg-destructive/10 border-destructive/20 text-destructive',
    info: 'bg-blue-500/10 border-blue-500/20 text-blue-500',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-500',
  }

  const Icon = icons[notification.type] || Info

  return (
    <motion.div
      initial={{ opacity: 0, x: 100, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="pointer-events-auto"
    >
      <div className={cn(
        "flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur-xl max-w-md",
        colors[notification.type]
      )}>
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm">{notification.title}</p>
          <p className="text-sm opacity-90 mt-1">{notification.message}</p>
        </div>
        <button
          onClick={onRemove}
          className="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  )
}
