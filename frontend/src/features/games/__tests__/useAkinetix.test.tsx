import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock } from 'vitest';
import { useAkinetix } from '../hooks/useAkinetix';
import { akinetixService } from '../services/akinetixService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock du service
vi.mock('../services/akinetixService');

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useAkinetix Hook', () => {
  it('devrait charger l\'état du jeu au montage', async () => {
    const mockState = { history: [], currentQuestion: 'Test?', gameOver: false };
    (akinetixService.getState as Mock).mockResolvedValue(mockState);

    const { result } = renderHook(() => useAkinetix(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameState).toEqual(mockState);
  });
});
