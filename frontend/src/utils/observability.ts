import * as Sentry from "@sentry/react";
import posthog from 'posthog-js';

export const initObservability = () => {
  // --- SENTRY (Error Tracking) ---
  // Note: DSN à configurer via variable d'environnement dans un vrai projet
  if (import.meta.env.VITE_SENTRY_DSN) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
      ],
      // Performance Monitoring
      tracesSampleRate: 1.0,
      // Session Replay
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      environment: import.meta.env.MODE,
    });
  }

  // --- POSTHOG (Product Analytics) ---
  if (import.meta.env.VITE_POSTHOG_KEY) {
    posthog.init(import.meta.env.VITE_POSTHOG_KEY, {
      api_host: import.meta.env.VITE_POSTHOG_HOST || 'https://eu.posthog.com',
      capture_pageview: true, // Capture automatique des changements de page
      persistence: 'localStorage+cookie',
    });
  }
};

// Utilitaire pour capturer des événements personnalisés
export const trackEvent = (name: string, properties?: Record<string, unknown>) => {
  posthog.capture(name, properties);
};
