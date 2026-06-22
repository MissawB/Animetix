import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { VisionState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { visionService } from '../visionService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);
const state = (): VisionState => ({}) as VisionState;

describe('visionService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState reads the state endpoint', async () => {
    const s = state();
    mocked.mockResolvedValue(s);
    expect(await visionService.getState()).toBe(s);
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vision/state/');
  });

  it('startGame POSTs to start', async () => {
    mocked.mockResolvedValue(state());
    await visionService.startGame();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vision/start/', { method: 'POST' });
  });

  it('submitGuess POSTs the description', async () => {
    mocked.mockResolvedValue(state());
    await visionService.submitGuess('a red mecha');
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/vision/guess/', {
      method: 'POST',
      body: JSON.stringify({ description: 'a red mecha' }),
    });
  });
});
