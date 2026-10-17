/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Civic Design Tokens (Phase 19.1 Foundation)
        gov: {
          navy: {
            DEFAULT: '#0f3460',
            dark: '#0a2342',
            light: '#162447',
          },
          accent: {
            DEFAULT: '#d97706',
            hover: '#b45309',
            light: '#fef3c7',
          },
          bg: '#f8fafc',
          surface: '#ffffff',
          border: '#e2e8f0',
          text: {
            DEFAULT: '#1e293b',
            muted: '#64748b',
            light: '#94a3b8',
          },
          success: {
            DEFAULT: '#15803d',
            bg: '#dcfce7',
          },
          warning: {
            DEFAULT: '#b45309',
            bg: '#fef3c7',
          },
          danger: {
            DEFAULT: '#b91c1c',
            bg: '#fee2e2',
          },
          info: {
            DEFAULT: '#0369a1',
            bg: '#e0f2fe',
          },
        },
      },
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          'ui-monospace',
          'SFMono-Regular',
          'monospace',
        ],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
    },
  },
  plugins: [],
}
