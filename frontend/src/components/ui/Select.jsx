import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export const Select = React.forwardRef(
  (
    {
      className,
      id,
      label,
      helperText,
      error,
      errorText,
      required = false,
      disabled = false,
      options,
      children,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId()
    const selectId = id || (label ? generatedId : undefined)
    const activeError = errorText || (typeof error === 'string' ? error : null)
    const hasError = Boolean(error || activeError)

    const helperId = helperText && selectId ? `${selectId}-helper` : undefined
    const errorId = activeError && selectId ? `${selectId}-error` : undefined
    const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-gov-text"
          >
            {label}
            {required && <span className="ml-1 text-gov-danger" aria-hidden="true">*</span>}
          </label>
        )}

        <div className="relative">
          <select
            id={selectId}
            ref={ref}
            disabled={disabled}
            required={required}
            aria-invalid={hasError}
            aria-describedby={describedBy}
            className={cn(
              'flex h-10 w-full appearance-none rounded-md border border-gov-border bg-gov-surface px-3 py-2 pr-10 text-sm text-gov-text shadow-sm transition-colors cursor-pointer',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gov-navy focus-visible:ring-offset-1 focus-visible:border-gov-navy',
              'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:opacity-60',
              hasError &&
                'border-gov-danger text-gov-danger focus-visible:ring-gov-danger focus-visible:border-gov-danger',
              className
            )}
            {...props}
          >
            {options
              ? options.map((opt) => (
                  <option
                    key={opt.value ?? opt.id ?? String(opt)}
                    value={opt.value ?? opt.id ?? String(opt)}
                    disabled={opt.disabled}
                  >
                    {opt.label ?? opt.name ?? String(opt)}
                  </option>
                ))
              : children}
          </select>

          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-gov-text-muted">
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          </div>
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

Select.displayName = 'Select'

export default Select
