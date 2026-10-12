import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'badge inline-flex items-center gap-1.5 font-medium transition-colors select-none',
  {
    variants: {
      variant: {
        success: 'badge-success',
        warning: 'badge-warning',
        danger: 'badge-danger',
        open: 'badge-open',
        urgent: 'badge-urgent',
        'warning-subtle': 'badge-warning-subtle',
        neutral: 'badge-neutral',
        gov: 'badge-gov',
        info: 'badge-info',
        outline: 'border border-gov-border bg-gov-surface text-gov-text',
      },
      size: {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-xs px-2.5 py-1',
        lg: 'text-sm px-3 py-1',
      },
    },
    defaultVariants: {
      variant: 'neutral',
      size: 'md',
    },
  }
)

export const Badge = React.forwardRef(
  (
    {
      className,
      variant = 'neutral',
      size = 'md',
      dot = false,
      icon,
      children,
      ...props
    },
    ref
  ) => {
    // Determine dot class according to variant
    const dotVariantMap = {
      success: 'dot-success',
      warning: 'dot-warning',
      danger: 'dot-danger',
      neutral: 'dot-neutral',
      open: 'dot-success',
      urgent: 'dot-danger',
      'warning-subtle': 'dot-warning',
    }

    const dotClass = dotVariantMap[variant] || 'dot-neutral'

    return (
      <span
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      >
        {dot && <span className={cn('badge-dot', dotClass)} aria-hidden="true" />}
        {icon && <span className="inline-flex shrink-0 items-center">{icon}</span>}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export default Badge
