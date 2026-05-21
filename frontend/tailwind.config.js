/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['class', '[data-bs-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        manga: ['Montserrat', 'sans-serif'],
        brush: ['"Permanent Marker"', 'cursive'],
      },
      colors: {
        'anime-accent': '#fdb913',
        'anime-accent-dark': '#d97706',
        
        // Light Mode
        'anime-light-bg': '#f1f3f5',
        'anime-light-text': '#1a1a2e',
        'anime-light-card': '#ffffff',
        
        // Dark Mode
        'anime-dark-bg': '#0f0f1a',
        'anime-dark-text': '#f1f2f6',
        'anime-dark-card': '#1a1a2e',
        
        // Core Game Colors (Retained from previous iteration)
        'anime-purple': '#7c3aed',
        'anime-pink': '#ec4899',
        'anime-cyan': '#06b6d4',
        'anime-success': '#10b981',
        'anime-error': '#ef4444',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(253, 185, 19, 0.5)' },
          '50%': { boxShadow: '0 0 30px rgba(217, 119, 6, 0.8)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
    },
  },
  plugins: [],
}

