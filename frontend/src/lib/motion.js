import { useReducedMotion } from 'motion/react'

/**
 * Motion configuration and variant presets for SchemeSetu.
 * Designed to provide subtle, professional civic transitions while
 * strictly respecting `prefers-reduced-motion`.
 */

export const transitions = {
  default: { duration: 0.2, ease: [0.16, 1, 0.3, 1] },
  gentle: { duration: 0.25, ease: 'easeOut' },
  subtle: { duration: 0.15, ease: 'easeInOut' },
}

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: transitions.default,
}

export const fadeInUp = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
  transition: transitions.gentle,
}

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.05,
    },
  },
}

/**
 * Hook to check if citizen requests reduced motion.
 * Used for components that need manual fallback behavior.
 */
export function useAccessibleMotion() {
  const shouldReduceMotion = useReducedMotion()
  return {
    shouldReduceMotion,
    fadeIn: shouldReduceMotion ? { initial: {}, animate: {} } : fadeIn,
    fadeInUp: shouldReduceMotion ? { initial: {}, animate: {} } : fadeInUp,
  }
}
