/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Agricultural theme colors
        soil: {
          50: '#f7f3f0',
          100: '#ede4dd',
          200: '#dbc8ba',
          300: '#c4a793',
          400: '#b08a70',
          500: '#9c7556',
          600: '#825f49',
          700: '#6b4d3e',
          800: '#5a4037',
          900: '#4d3730',
        },
        health: {
          excellent: '#16a34a', // green-600
          good: '#65a30d',      // lime-600
          fair: '#ca8a04',      // yellow-600
          poor: '#dc2626',      // red-600
        },
        crop: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce 2s infinite',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
} 