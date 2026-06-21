import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ClassicGameState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { classicGameService } from '../classicService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): ClassicGameState => ({} as ClassicGameState);

describe('classicGameService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState calls the state endpoint and returns the value', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await classicGameService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/classic/state/');
    expect(result).toBe(state);
  });

  it('start posts default media type and difficulty', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await classicGameService.start();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/classic/start/', {
      method: 'POST',
      body: JSON.stringify({ media_type: 'Anime', difficulty: 'Normal' }),
    });
    expect(result).toBe(state);
  });

  it('start posts provided media type and difficulty', async () => {
    mocked.mockResolvedValue(makeState());

    await classicGameService.start('Manga', 'Hard');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/classic/start/', {
      method: 'POST',
      body: JSON.stringify({ media_type: 'Manga', difficulty: 'Hard' }),
    });
  });

  it('submit posts the guess', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await classicGameService.submit({ guess: 'Naruto' });

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/classic/guess/', {
      method: 'POST',
      body: JSON.stringify({ guess: 'Naruto' }),
    });
    expect(result).toBe(state);
  });
});
