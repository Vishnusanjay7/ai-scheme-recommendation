import * as React from 'react'
import { cn } from '@/lib/utils'

export const Skeleton = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    aria-hidden="true"
    className={cn(
      'animate-pulse motion-reduce:animate-none rounded bg-slate-200/80',
      className
    )}
    {...props}
  />
))
Skeleton.displayName = 'Skeleton'

export function SkeletonText({ lines = 3, className }) {
  return (
    <div className={cn('space-y-2 w-full', className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            'h-4',
            i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  )
}

export function SkeletonAvatar({ size = 'md', className }) {
  const sizeMap = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-14 w-14',
  }

  return (
    <Skeleton
      className={cn('rounded-full shrink-0', sizeMap[size] || sizeMap.md, className)}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard({ className }) {
  return (
    <div
      className={cn(
        'rounded-lg border border-gov-border/80 bg-gov-surface p-6 space-y-4 shadow-sm',
        className
      )}
      aria-hidden="true"
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-24 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-6 w-3/4" />
      <SkeletonText lines={2} />
      <div className="flex items-center justify-between pt-2">
        <Skeleton className="h-9 w-28 rounded-md" />
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>
    </div>
  )
}

export function SkeletonList({ count = 3, className }) {
  return (
    <div className={cn('space-y-3 w-full', className)} aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-md border border-gov-border/60 bg-gov-surface p-3"
        >
          <SkeletonAvatar size="sm" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-3 w-3/4" />
          </div>
          <Skeleton className="h-8 w-20 rounded-md shrink-0" />
        </div>
      ))}
    </div>
  )
}

export default Skeleton
