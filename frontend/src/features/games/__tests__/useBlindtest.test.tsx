import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock } from 'vitest';
import { useBlindtest } from '../hooks/useBlindtest';
import { blindtestService } from '../services/blindtestService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('../services/blindtestService');

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useBlindtest Hook', () => {
  it('devrait charger l\'état du jeu blindtest', async () => {
    const mockState = { guesses: [], gameOver: false, secret_title: 'Test Anime' };
    (blindtestService.getState as Mock).mockResolvedValue(mockState);

    const { result } = renderHook(() => useBlindtest(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameState).toEqual(mockState);
  });
});
