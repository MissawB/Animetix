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
        maximumFileSizeToCacheInBytes: 6000000, // 6MB pour autoriser plotly
        navigateFallback: '/static/index.html',
        navigateFallbackDenylist: [/^\/api\//]
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