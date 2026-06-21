import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEmoji } from '../useEmoji';
import { emojiService } from '../../services/emojiService';
import { EmojiState } from '../../../../types';

vi.mock('../../services/emojiService');

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const mockState = (overrides: Partial<EmojiState> = {}): EmojiState =>
  ({ status: 'playing', ...overrides } as unknown as EmojiState);

describe('useEmoji', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the emoji state from getState', async () => {
    const state = mockState();
    (emojiService.getState as Mock).mockResolvedValue(state);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameState).toEqual(state);
  });

  it('writes the new state to the cache after a guess', async () => {
    const initial = mockState();
    const next = mockState({ status: 'won' } as Partial<EmojiState>);
    (emojiService.getState as Mock).mockResolvedValue(initial);
    (emojiService.submit as Mock).mockResolvedValue(next);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.handleGuess({ guess: 'One Piece' });
    });

    expect((emojiService.submit as Mock).mock.calls[0][0]).toEqual({ guess: 'One Piece' });
    await waitFor(() => expect(result.current.gameState).toEqual(next));
  });

  it('restart refetches the state', async () => {
    const state = mockState();
    (emojiService.getState as Mock).mockResolvedValue(state);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      result.current.restart();
    });
    await waitFor(() => expect((emojiService.getState as Mock).mock.calls.length).toBeGreaterThanOrEqual(2));
  });
});
