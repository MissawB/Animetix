/// <reference types="vitest/config" />
import { defineConfig, PluginOption } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
import { VitePWA } from 'vite-plugin-pwa';

// https://vite.dev/config/
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { storybookTest } from '@storybook/addon-vitest/vitest-plugin';
import { playwright } from '@vitest/browser-playwright';
const dirname = typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url));

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
export default defineConfig({
  base: '/static/',
  plugins: [
    react(), 
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons.svg'],
      manifest: {
        name: 'Animetix',
        short_name: 'Animetix',
        description: 'The Next-Gen Anime Archetype Engine',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        icons: [
          {
            src: 'favicon.svg',
            sizes: '192x192',
            type: 'image/svg+xml'
          },
          {
            src: 'favicon.svg',
            sizes: '512x512',
            type: 'image/svg+xml'
          }
        ]
      },
      workbox: {
        // On NE précache PAS les très gros chunks (ex. plotly-vendor ~4,6 Mo) : ils
        // alourdissaient l'install du SW (~7,5 Mo) pour tous les visiteurs, même ceux
        // qui n'ouvrent jamais de page Plotly/3D (routes lazy). Limite à 2 Mo →
        // ces chunks sont mis en cache à la demande via runtimeCaching ci-dessous
        // (offline préservé après la 1re visite de la page concernée).
        maximumFileSizeToCacheInBytes: 2000000, // 2 Mo
        // Exclusion explicite du chunk plotly (~4,6 Mo) du manifeste de précache
        // (sinon vite-plugin-pwa lève une erreur de build). Servi via runtimeCaching.
        globIgnores: ['**/plotly-vendor-*.js'],
        navigateFallback: '/static/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            // Chunks JS/CSS hashés non précachés (plotly, three.js, pages lourdes…)
            urlPattern: /\/static\/assets\/.*\.(?:js|css)$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'static-assets-runtime',
              expiration: { maxEntries: 80, maxAgeSeconds: 60 * 60 * 24 * 30 }
            }
          }
        ]
      }
    }),
    visualizer({
    filename: 'stats.html',
    // Fichier d'analyse généré après le build
    open: false,
    gzipSize: true
  }) as unknown as PluginOption],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom') || id.includes('node_modules/react-router-dom')) {
            return 'react-vendor';
          }
          if (id.includes('node_modules/@tanstack')) {
            return 'query-vendor';
          }
          if (id.includes('node_modules/plotly.js') || id.includes('node_modules/react-plotly.js')) {
            return 'plotly-vendor';
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'ui-vendor';
          }
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  test: {
    exclude: ['node_modules/**', 'dist/**', '.git/**', '.cache/**', 'e2e/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text-summary', 'text', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      // On exclut le non-testable (types, stories, tests, bootstrap, déclarations)
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.stories.{ts,tsx}',
        'src/**/*.test.{ts,tsx}',
        'src/**/__tests__/**',
        'src/test/**',
        'src/types/**',
        'src/main.tsx',
      ],
      // Plancher anti-régression (baseline ≈ 29 % stmts après les campagnes
      // services/utils/hooks + composants + pages). Remonter, jamais baisser.
      thresholds: {
        statements: 28,
        branches: 22,
        functions: 27,
        lines: 28,
      },
    },
    projects: [{
      extends: true,
      test: {
        name: 'unit',
        globals: true,
        environment: 'jsdom',
        setupFiles: './src/test/setup.ts'
      }
    }, {
      extends: true,
      plugins: [
      // The plugin will run tests for the stories defined in your Storybook config
      // See options at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon#storybooktest
      storybookTest({
        configDir: path.join(dirname, '.storybook')
      })],
      test: {
        name: 'storybook',
        browser: {
          enabled: true,
          headless: true,
          provider: playwright({}),
          instances: [{
            browser: 'chromium'
          }]
        }
      }
    }]
  }
});