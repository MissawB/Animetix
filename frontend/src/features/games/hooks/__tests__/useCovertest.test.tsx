import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { CovertestState } from '../../../../types';
import { covertestService } from '../../services/covertestService';
import { useCovertest } from '../useCovertest';

vi.mock('../../services/covertestService', () => ({
  covertestService: { getState: vi.fn(), submit: vi.fn() },
}));
const getState = vi.mocked(covertestService.getState);
const submit = vi.mocked(covertestService.submit);
const state = (over: Partial<CovertestState> = {}): CovertestState => ({ ...over }) as CovertestState;

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useCovertest', () => {
  beforeEach(() => vi.clearAllMocks());

  it('loads the game state', async () => {
    const s = state();
    getState.mockResolvedValue(s);
    const { result } = renderHook(() => useCovertest(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(getState).toHaveBeenCalled();
    expect(result.current.gameState).toBe(s);
  });

  it('handleGuess submits and writes the new state into the cache', async () => {
    getState.mockResolvedValue(state());
    const next = { winner: true } as unknown as CovertestState;
    submit.mockResolvedValue(next);
    const { result } = renderHook(() => useCovertest(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.handleGuess({ guess: 'the spy' });
    });

    // TanStack Query v5 calls mutationFn(variables, context) — assert just the variables.
    expect(submit.mock.calls[0][0]).toEqual({ guess: 'the spy' });
    // onSuccess writes the result into the cache (compare by value: react-query
    // structural-sharing may hand back a fresh reference).
    await waitFor(() => expect(result.current.gameState).toEqual({ winner: true }));
  });
});
