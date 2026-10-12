import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Standard utility function for combining class names with Tailwind conflict resolution.
 * Dependency-safe and adheres to shadcn/ui pattern.
 *
 * @param {...any} inputs - Class names, expressions, or conditional objects.
 * @returns {string} Merged, deduplicated className string.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
