/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/backend/animetix/templates/**/*.html",
    "./src/backend/animetix/static/**/*.js",
  ],
  darkMode: ['selector', '[data-bs-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        yellow: {
          400: '#fdb913',
          600: '#d97706',
        },
        navy: {
          700: '#1e1e2f',
          800: '#1a1a2e',
          900: '#0f0f1a',
        }
      }
    },
  },
  plugins: [],
}
