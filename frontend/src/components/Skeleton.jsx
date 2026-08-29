import { motion } from 'framer-motion'
import { cn } from '../lib/utils'

export function Skeleton({ className, ...props }) {
  return (
    <motion.div
      animate={{
        opacity: [0.4, 0.9, 0.4],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      className={cn('bg-[var(--surface-2)] border border-[var(--line)] rounded-md', className)}
      {...props}
    />
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--surface-1)] p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton className="h-8 w-8 rounded-full" />
      </div>
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-4 rounded" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--surface-1)] p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <Skeleton className="h-4 w-12" />
      </div>
      <Skeleton className="h-8 w-20 mb-2" />
      <Skeleton className="h-4 w-24" />
    </div>
  )
}

export function TableRowSkeleton() {
  return (
    <div className="flex items-center gap-4 p-4 border-b border-[var(--line)]">
      <Skeleton className="h-10 w-10 rounded-lg" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <Skeleton className="h-8 w-20" />
    </div>
  )
}

export function ListSkeleton({ count = 3 }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <TableRowSkeleton key={i} />
      ))}
    </div>
  )
}

export default Skeleton
