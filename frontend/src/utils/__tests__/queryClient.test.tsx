import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClientProvider, useQuery } from '@tanstack/react-query';

// Neutralise la persistance IndexedDB (indisponible sous jsdom).
vi.mock('../persister', () => ({
  createPersister: () => ({
    persistClient: async () => {},
    restoreClient: async () => undefined,
    removeClient: async () => {},
  }),
}));

import { queryClient } from '../queryClient';

describe('queryClient', () => {
  it('refetches cached queries on mount so navigation never shows stale data', async () => {
    // Régression : avec un staleTime de 5 min persisté 24h, revenir sur une
    // page remontait la donnée en cache SANS refetch — il fallait F5 pour voir
    // l'état à jour (score du daily, XP, partie en cours...).
    const key = ['nav-freshness-regression'];
    queryClient.setQueryData(key, 'cached');
    const queryFn = vi.fn().mockResolvedValue('fresh');

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(
      () => useQuery({ queryKey: key, queryFn }),
      { wrapper },
    );

    // Le cache est servi immédiatement (pas d'écran de chargement)...
    expect(result.current.data).toBe('cached');
    // ...mais une revalidation part en arrière-plan à chaque montage.
    await waitFor(() => expect(queryFn).toHaveBeenCalled());
    await waitFor(() => expect(result.current.data).toBe('fresh'));
  });
});
