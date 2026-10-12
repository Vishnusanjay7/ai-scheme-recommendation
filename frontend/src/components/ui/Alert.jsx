import * as React from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const defaultIcons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: AlertCircle,
}

export const Alert = React.forwardRef(
  (
    {
      className,
      variant = 'info',
      title,
      description,
      children,
      icon,
      dismissible = false,
      onDismiss,
      ...props
    },
    ref
  ) => {
    const [dismissed, setDismissed] = React.useState(false)

    if (dismissed) {
      return null
    }

    const IconComponent = icon !== undefined ? icon : defaultIcons[variant] || Info

    // Map directly to existing CSS classes: alert alert-info, alert-success, alert-danger, alert-warning
    const variantClass =
      variant === 'danger'
        ? 'alert-danger'
        : variant === 'success'
          ? 'alert-success'
          : variant === 'warning'
            ? 'alert-warning'
            : 'alert-info'

    const handleDismiss = () => {
      setDismissed(true)
      if (onDismiss) {
        onDismiss()
      }
    }

    return (
      <div
        ref={ref}
        role="alert"
        className={cn('alert', variantClass, 'relative flex items-start gap-3 p-4 rounded-md', className)}
        {...props}
      >
        {IconComponent && (
          <div className="mt-0.5 shrink-0">
            {React.isValidElement(IconComponent) ? (
              IconComponent
            ) : (
              <IconComponent className="h-5 w-5" aria-hidden="true" />
            )}
          </div>
        )}

        <div className="flex-1 space-y-1">
          {title && <h5 className="font-semibold text-sm leading-none">{title}</h5>}
          {description && <div className="text-sm opacity-90 leading-relaxed">{description}</div>}
          {children && <div className="text-sm opacity-90 leading-relaxed">{children}</div>}
        </div>

        {dismissible && (
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Dismiss alert"
            className="shrink-0 rounded p-1 opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-1 cursor-pointer transition-opacity"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export default Alert
