/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        base: {
          950: '#09090B', // Pure deep matte zinc
          900: '#18181B', // Elevated panels
          800: '#27272A', // Hover states
        },
        verdict: {
          buy: '#10B981',    // Matte Emerald
          monitor: '#0EA5E9', // Matte Sky Blue
          caution: '#F59E0B', // Matte Amber
          avoid: '#EF4444',   // Matte Red
        }
      }
    },
  },
  plugins: [],
}