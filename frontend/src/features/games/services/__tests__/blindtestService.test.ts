import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { BlindtestState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { blindtestService } from '../blindtestService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): BlindtestState => ({} as BlindtestState);

describe('blindtestService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState calls the state endpoint and returns the value', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await blindtestService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/state/');
    expect(result).toBe(state);
  });

  it('startGame posts to the start endpoint', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await blindtestService.startGame();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/start/', { method: 'POST' });
    expect(result).toBe(state);
  });

  it('submitGuess posts the guess', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await blindtestService.submitGuess('One Piece');

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/blindtest/guess/', {
      method: 'POST',
      body: JSON.stringify({ guess: 'One Piece' }),
    });
    expect(result).toBe(state);
  });
});
