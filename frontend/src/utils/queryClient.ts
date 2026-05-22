import { QueryClient } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createPersister } from './persister';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // Conserver en cache 24h
      staleTime: 1000 * 60 * 5,    // Considérer "frais" pendant 5 min
      retry: 2,
    },
  },
});

// Activation de la persistance avec IndexedDB
persistQueryClient({
  queryClient,
  persister: createPersister(),
  maxAge: 1000 * 60 * 60 * 24, // Persistance valide 24h
});
