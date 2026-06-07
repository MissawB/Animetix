import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, Mock } from 'vitest';
import { useVision } from '../../../features/games/hooks/useVision';
import { visionService } from '../../../features/games/services/visionService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('../../../features/games/services/visionService');

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useVision Hook', () => {
  it('devrait charger l\'état du jeu vision', async () => {
    const mockState = { guesses: [], gameOver: false, image_url: 'test.jpg' };
    (visionService.getState as Mock).mockResolvedValue(mockState);

    const { result } = renderHook(() => useVision(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameState).toEqual(mockState);
  });
});




