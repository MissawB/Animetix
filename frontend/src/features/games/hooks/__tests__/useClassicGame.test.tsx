import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useClassicGame } from '../useClassicGame';
import { classicGameService } from '../../services/classicService';
import { ClassicGameState } from '../../../../types';

vi.mock('../../services/classicService');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const mockState = (overrides: Partial<ClassicGameState> = {}): ClassicGameState =>
  ({ status: 'playing', ...overrides } as unknown as ClassicGameState);

describe('useClassicGame', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns state from getState on success', async () => {
    const state = mockState();
    (classicGameService.getState as Mock).mockResolvedValue(state);

    const { result } = renderHook(() => useClassicGame(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameState).toEqual(state);
    expect(classicGameService.start).not.toHaveBeenCalled();
  });

  it('falls back to start() when getState throws', async () => {
    const started = mockState({ status: 'started' } as Partial<ClassicGameState>);
    (classicGameService.getState as Mock).mockRejectedValue(new Error('no state'));
    (classicGameService.start as Mock).mockResolvedValue(started);

    const { result } = renderHook(() => useClassicGame(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(classicGameService.start).toHaveBeenCalledTimes(1);
    expect(result.current.gameState).toEqual(started);
  });

  it('updates the cached state after a guess (handleGuess)', async () => {
    const initial = mockState();
    const next = mockState({ status: 'won' } as Partial<ClassicGameState>);
    (classicGameService.getState as Mock).mockResolvedValue(initial);
    (classicGameService.submit as Mock).mockResolvedValue(next);

    const { result } = renderHook(() => useClassicGame(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.handleGuess({ guess: 'Naruto' });
    });

    expect((classicGameService.submit as Mock).mock.calls[0][0]).toEqual({ guess: 'Naruto' });
    await waitFor(() => expect(result.current.gameState).toEqual(next));
  });

  it('exposes a restart function that invalidates the query', async () => {
    const state = mockState();
    (classicGameService.getState as Mock).mockResolvedValue(state);

    const { result } = renderHook(() => useClassicGame(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(typeof result.current.restart).toBe('function');
    await act(async () => {
      result.current.restart();
    });
    // getState refetched on invalidation
    await waitFor(() => expect((classicGameService.getState as Mock).mock.calls.length).toBeGreaterThanOrEqual(2));
  });
});
