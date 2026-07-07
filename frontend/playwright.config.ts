import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,
  expect: {
    timeout: 15000,
  },
  // En CI : rapport HTML (jamais auto-ouvert) + annotations GitHub sur les échecs.
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['github']]
    : 'html',
  use: {
    baseURL: 'http://localhost:5173',
    locale: 'fr-FR',
    // Artefacts de debug produits UNIQUEMENT en cas d'échec (coût ~nul en succès) :
    // trace rejouable, capture d'écran et vidéo — récupérés en CI via upload-artifact.
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Exécuter le serveur de dev local avant de lancer les tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
