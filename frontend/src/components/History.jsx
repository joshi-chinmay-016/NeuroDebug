import { motion } from 'framer-motion'
import { Search, Filter, Download, Trash2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../lib/utils'

const mockHistory = [
  {
    id: 1,
    code: 'def calculate_sum(a, b):\n    return a + b\n\nresult = calculate_sum(10, "20")',
    errorType: 'TypeError',
    status: 'verified',
    timestamp: '2 hours ago',
    duration: '1.2s',
  },
  {
    id: 2,
    code: 'def process_data(items):\n    for item in items:\n        print(item[missing_key])',
    errorType: 'KeyError',
    status: 'failed',
    timestamp: '5 hours ago',
    duration: '0.8s',
  },
  {
    id: 3,
    code: 'class User:\n    def __init__(self, name):\n        self.name = name\n\nuser = User()',
    errorType: 'TypeError',
    status: 'verified',
    timestamp: '1 day ago',
    duration: '1.5s',
  },
  {
    id: 4,
    code: 'import requests\n\nresponse = requests.get("https://api.example.com")\ndata = response.json()',
    errorType: 'ConnectionError',
    status: 'verified',
    timestamp: '2 days ago',
    duration: '2.1s',
  },
]

export default function History() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const filteredHistory = mockHistory.filter((item) => {
    const matchesSearch = item.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.errorType.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight">Debug History</h1>
        <p className="text-muted-foreground mt-2">
          View and manage your past debugging sessions
        </p>
      </motion.div>

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
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">All Status</option>
            <option value="verified">Verified</option>
            <option value="failed">Failed</option>
          </select>
          <button className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors border border-border/40 bg-background hover:bg-accent h-10 px-4">
            <Filter className="h-4 w-4 mr-2" />
            More Filters
          </button>
        </div>
      </motion.div>

      {/* History List */}
      <div className="space-y-4">
        {filteredHistory.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 + index * 0.05 }}
            className="group rounded-xl border border-border/40 bg-card p-6 shadow-sm hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "p-2 rounded-lg",
                    item.status === 'verified'
                      ? "bg-green-500/10"
                      : "bg-red-500/10"
                  )}
                >
                  {item.status === 'verified' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold">{item.errorType}</h3>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                    <Clock className="h-3 w-3" />
                    <span>{item.timestamp}</span>
                    <span>•</span>
                    <span>{item.duration}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-2 rounded-md hover:bg-accent transition-colors">
                  <Download className="h-4 w-4 text-muted-foreground" />
                </button>
                <button className="p-2 rounded-md hover:bg-destructive/10 transition-colors">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </button>
              </div>
            </div>

            <div className="rounded-lg bg-muted/50 p-4 overflow-hidden">
              <pre className="text-sm font-mono text-muted-foreground whitespace-pre-wrap">
                {item.code}
              </pre>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {filteredHistory.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Clock className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No history found</h3>
          <p className="text-muted-foreground">
            {searchQuery || statusFilter !== 'all'
              ? 'Try adjusting your filters'
              : 'Start debugging to build your history'}
          </p>
        </motion.div>
      )}
    </div>
  )
}
