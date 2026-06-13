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
        'brand-primary': 'rgb(var(--color-primary) / <alpha-value>)',
        'brand-secondary': 'rgb(var(--color-secondary) / <alpha-value>)',
        'brand-success': 'rgb(var(--color-success) / <alpha-value>)',
        'brand-danger': 'rgb(var(--color-danger) / <alpha-value>)',
        'brand-warning': 'rgb(var(--color-warning) / <alpha-value>)',
        'brand-accent': 'rgb(var(--color-accent) / <alpha-value>)',
        'brand-drift': 'var(--color-accent-drift)',
        'surface-bg': 'rgb(var(--color-bg) / <alpha-value>)',
        'surface-text': 'rgb(var(--color-text) / <alpha-value>)',
        'surface-card': 'rgb(var(--color-card) / <alpha-value>)',
        
        // Cyberpunk
        'cyberpunk-bg': '#050505',
        'cyberpunk-panel': 'rgba(255, 255, 255, 0.05)',
        'cyberpunk-panelBorder': 'rgba(255, 255, 255, 0.1)',
        'cyberpunk-neonCyan': '#00F3FF',
        'cyberpunk-neonMagenta': '#FF00FF',
        
        // Legacy compat (if needed)
        'anime-accent': 'rgb(var(--color-accent) / <alpha-value>)',
        'anime-success': 'rgb(var(--color-success) / <alpha-value>)',
        'anime-error': 'rgb(var(--color-danger) / <alpha-value>)',
      },
      borderRadius: {
        'token-card': 'var(--radius-card)',
        'token-button': 'var(--radius-button)',
      },
      borderWidth: {
        'token-card': 'var(--border-width-card)',
      },
      boxShadow: {
        'token-card': 'var(--shadow-card)',
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

