/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        gt: {
          bg: '#0a0f1a',
          surface: '#111827',
          surface2: '#1a2234',
          border: '#1f2937',
          text: '#e5e7eb',
          muted: '#9ca3af',
          accent: '#10b981',
          'accent-dim': '#059669',
          warn: '#f59e0b',
          danger: '#ef4444',
          skipped: '#6b7280',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
