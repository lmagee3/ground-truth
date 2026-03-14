/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        gt: {
          bg: '#0a0a0f',
          surface: '#0d0d14',
          surface2: '#111111',
          border: '#1a1a2e',
          text: '#e0e0e0',
          muted: '#888888',
          accent: '#00ff88',
          'accent-dim': '#00ff8855',
          warn: '#ff6b35',
          danger: '#ff5588',
          blue: '#3388ff',
          purple: '#aa55ff',
          skipped: '#666666',
        },
      },
      fontFamily: {
        mono: ['"SF Mono"', '"Fira Code"', '"Consolas"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
