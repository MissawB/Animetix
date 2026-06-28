import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { CovertestState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { covertestService } from '../covertestService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);
const state = (): CovertestState => ({}) as CovertestState;

describe('covertestService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState reads the state endpoint', async () => {
    const s = state();
    mocked.mockResolvedValue(s);
    expect(await covertestService.getState()).toBe(s);
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/covertest/state/', { skipToast: true });
  });

  it('submit POSTs the guess', async () => {
    mocked.mockResolvedValue(state());
    await covertestService.submit({ guess: 'the spy' });
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/covertest/guess/', {
      method: 'POST',
      body: JSON.stringify({ guess: 'the spy' }),
    });
  });

  it('start POSTs is_daily', async () => {
    mocked.mockResolvedValue(state());
    await covertestService.start();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/covertest/start/', {
      method: 'POST',
      body: JSON.stringify({ is_daily: false }),
    });
  });

  it('getTitles returns the titles array', async () => {
    mocked.mockResolvedValue({ titles: ['One Piece', 'Bleach'] });
    expect(await covertestService.getTitles()).toEqual(['One Piece', 'Bleach']);
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/covertest/titles/', { skipToast: true });
  });

  it('reveal POSTs to the reveal endpoint', async () => {
    mocked.mockResolvedValue(state());
    await covertestService.reveal();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/covertest/reveal/', { method: 'POST' });
  });
});
