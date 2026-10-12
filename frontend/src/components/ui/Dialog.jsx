import * as React from 'react'
import { X } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { cn } from '@/lib/utils'

export function Dialog({
  isOpen = false,
  onClose,
  title,
  description,
  children,
  footer,
  className,
  maxWidth = 'max-w-lg',
  showCloseButton = true,
}) {
  const titleId = React.useId()
  const descriptionId = React.useId()
  const contentRef = React.useRef(null)

  // Escape key handler
  React.useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose?.()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  // Prevent background scroll while open
  React.useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = originalOverflow
      }
    }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          role="presentation"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            aria-hidden="true"
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm"
          />

          {/* Modal Content */}
          <motion.div
            ref={contentRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={description ? descriptionId : undefined}
            tabIndex={-1}
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              'relative z-50 w-full rounded-lg border border-gov-border/80 bg-gov-surface p-6 text-gov-text shadow-xl',
              maxWidth,
              className
            )}
          >
            {/* Close Button */}
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                aria-label="Close dialog"
                className="absolute right-4 top-4 rounded-sm p-1 text-gov-text-muted hover:text-gov-text focus:outline-none focus:ring-2 focus:ring-gov-navy focus:ring-offset-2 transition-colors cursor-pointer"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}

            {/* Header */}
            {(title || description) && (
              <div className="space-y-1.5 pb-4">
                {title && (
                  <h3
                    id={titleId}
                    className="text-lg font-semibold leading-none tracking-tight text-gov-text"
                  >
                    {title}
                  </h3>
                )}
                {description && (
                  <p
                    id={descriptionId}
                    className="text-sm text-gov-text-muted leading-relaxed"
                  >
                    {description}
                  </p>
                )}
              </div>
            )}

            {/* Body */}
            <div className="py-2">{children}</div>

            {/* Footer */}
            {footer && (
              <div className="flex items-center justify-end gap-2 pt-4 border-t border-gov-border/60">
                {footer}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

export default Dialog
