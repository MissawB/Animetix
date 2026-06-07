import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock } from 'vitest';
import { useAkinetix } from '../../../features/games/hooks/useAkinetix';
import { akinetixService } from '../../../features/games/services/akinetixService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock du service
vi.mock('../../../features/games/services/akinetixService');

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



