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
  ({ media_type: 'Anime', ...overrides } as unknown as EmojiState);

describe('useEmoji', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not auto-start: no getState on mount, gameState undefined (chooser first)', () => {
    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    expect(emojiService.getState as Mock).not.toHaveBeenCalled();
    expect(result.current.gameState).toBeUndefined();
  });

  it('start() launches a game with type + difficulty and writes it to the cache', async () => {
    const started = mockState({ media_type: 'Manga', difficulty: 'Hard' });
    (emojiService.start as Mock).mockResolvedValue(started);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.start('Manga', 'Hard');
    });

    expect((emojiService.start as Mock).mock.calls[0]).toEqual(['Manga', 'Hard']);
    await waitFor(() => expect(result.current.gameState).toEqual(started));
  });

  it('writes the new state to the cache after a guess', async () => {
    const started = mockState();
    const next = mockState({ game_over: true });
    (emojiService.start as Mock).mockResolvedValue(started);
    (emojiService.submit as Mock).mockResolvedValue(next);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.start('Anime', 'Normal');
    });
    await waitFor(() => expect(result.current.gameState).toEqual(started));

    await act(async () => {
      await result.current.handleGuess({ guess: 'One Piece' });
    });

    expect((emojiService.submit as Mock).mock.calls[0][0]).toEqual({ guess: 'One Piece' });
    await waitFor(() => expect(result.current.gameState).toEqual(next));
  });

  it('reset clears the current game (back to chooser)', async () => {
    const started = mockState();
    (emojiService.start as Mock).mockResolvedValue(started);

    const { result } = renderHook(() => useEmoji(), { wrapper: makeWrapper() });
    await act(async () => {
      result.current.start('Anime', 'Normal');
    });
    await waitFor(() => expect(result.current.gameState).toEqual(started));

    await act(async () => {
      result.current.reset();
    });
    await waitFor(() => expect(result.current.gameState).toBeUndefined());
  });
});
