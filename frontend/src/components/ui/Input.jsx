import * as React from 'react'
import { cn } from '@/lib/utils'

export const Input = React.forwardRef(
  (
    {
      className,
      type = 'text',
      id,
      label,
      helperText,
      error,
      errorText,
      required = false,
      disabled = false,
      leftIcon,
      rightIcon,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId()
    const inputId = id || (label ? generatedId : undefined)
    const activeError = errorText || (typeof error === 'string' ? error : null)
    const hasError = Boolean(error || activeError)

    const helperId = helperText && inputId ? `${inputId}-helper` : undefined
    const errorId = activeError && inputId ? `${inputId}-error` : undefined
    const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gov-text"
          >
            {label}
            {required && <span className="ml-1 text-gov-danger" aria-hidden="true">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="pointer-events-none absolute left-3 flex items-center text-gov-text-muted">
              {leftIcon}
            </div>
          )}

          <input
            id={inputId}
            ref={ref}
            type={type}
            disabled={disabled}
            required={required}
            aria-invalid={hasError}
            aria-describedby={describedBy}
            className={cn(
              'flex h-10 w-full rounded-md border border-gov-border bg-gov-surface px-3 py-2 text-sm text-gov-text shadow-sm transition-colors',
              'placeholder:text-gov-text-muted/70',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gov-navy focus-visible:ring-offset-1 focus-visible:border-gov-navy',
              'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:opacity-60',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              hasError &&
                'border-gov-danger text-gov-danger focus-visible:ring-gov-danger focus-visible:border-gov-danger',
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 flex items-center text-gov-text-muted">
              {rightIcon}
            </div>
          )}
        </div>

        {activeError ? (
          <p id={errorId} className="text-xs text-gov-danger font-medium" role="alert">
            {activeError}
          </p>
        ) : helperText ? (
          <p id={helperId} className="text-xs text-gov-text-muted">
            {helperText}
          </p>
        ) : null}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
