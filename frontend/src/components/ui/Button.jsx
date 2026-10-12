import * as React from 'react'
import { cva } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { motion } from 'motion/react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary:
          'bg-gov-navy text-white hover:bg-gov-navy-light active:bg-gov-navy-dark focus-visible:ring-gov-navy shadow-sm',
        secondary:
          'bg-gov-accent text-white hover:bg-gov-accent-hover active:bg-amber-800 focus-visible:ring-gov-accent shadow-sm',
        outline:
          'border border-gov-border bg-gov-surface text-gov-text hover:bg-slate-100 hover:text-gov-text active:bg-slate-200 focus-visible:ring-gov-navy shadow-sm',
        ghost:
          'text-gov-text hover:bg-slate-100 active:bg-slate-200 focus-visible:ring-gov-navy',
        danger:
          'bg-gov-danger text-white hover:bg-red-800 active:bg-red-900 focus-visible:ring-gov-danger shadow-sm',
        success:
          'bg-gov-success text-white hover:bg-green-800 active:bg-green-900 focus-visible:ring-gov-success shadow-sm',
        link:
          'text-gov-navy underline-offset-4 hover:underline focus-visible:ring-gov-navy p-0 h-auto',
      },
      size: {
        sm: 'h-8 px-3 text-xs rounded-md gap-1.5',
        md: 'h-10 px-4 py-2 text-sm rounded-md gap-2',
        lg: 'h-12 px-6 text-base rounded-md gap-2.5',
        icon: 'h-10 w-10 p-0 rounded-md',
        'icon-sm': 'h-8 w-8 p-0 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

export const Button = React.forwardRef(
  (
    {
      className,
      variant,
      size,
      isLoading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      children,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading

    return (
      <motion.button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isLoading}
        whileTap={{ scale: isDisabled ? 1 : 0.98 }}
        transition={{ duration: 0.1 }}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-current" aria-hidden="true" />
            <span className="opacity-90">{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="inline-flex shrink-0 items-center">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="inline-flex shrink-0 items-center">{rightIcon}</span>}
          </>
        )}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'

export default Button
