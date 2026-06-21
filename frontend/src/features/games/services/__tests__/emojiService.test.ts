import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { EmojiState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { emojiService } from '../emojiService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): EmojiState => ({} as EmojiState);

describe('emojiService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState calls the state endpoint and returns the value', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await emojiService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/emoji/state/');
    expect(result).toBe(state);
  });

  it('submit posts the guess', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await emojiService.submit({ guess: 'Bleach' });

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/emoji/guess/', {
      method: 'POST',
      body: JSON.stringify({ guess: 'Bleach' }),
    });
    expect(result).toBe(state);
  });
});
