import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';
import * as Sentry from '@sentry/react';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createPersister } from './persister';

// Reporting centralisé vers Sentry. Les toasts utilisateur sont déjà émis par
// `apiClient` (sauf `skipToast`) — on n'en ajoute pas ici pour éviter les doublons.
const reportError = (error: unknown, source: 'query' | 'mutation') => {
  Sentry.captureException(error, { tags: { source: `react-query:${source}` } });
};

// Pas de retry sur les erreurs client (4xx, ex. 401/403/404) — réessayer est inutile
// et masque le vrai problème. `status` est attaché par `apiClient`.
const retryUnlessClientError = (failureCount: number, error: unknown) => {
  const status = (error as { status?: number } | null)?.status;
  if (typeof status === 'number' && status >= 400 && status < 500) return false;
  return failureCount < 2;
};

export const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: (error) => reportError(error, 'query') }),
  mutationCache: new MutationCache({ onError: (error) => reportError(error, 'mutation') }),
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // Conserver en cache 24h
      staleTime: 1000 * 60 * 5,    // Considérer "frais" pendant 5 min
      retry: retryUnlessClientError,
    },
  },
});

// Activation de la persistance avec IndexedDB
persistQueryClient({
  queryClient,
  persister: createPersister(),
  maxAge: 1000 * 60 * 60 * 24, // Persistance valide 24h
});
