import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AkinetixState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { akinetixService } from '../akinetixService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);
const state = (): AkinetixState => ({}) as AkinetixState;

describe('akinetixService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState reads the state endpoint', async () => {
    const s = state();
    mocked.mockResolvedValue(s);
    expect(await akinetixService.getState()).toBe(s);
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/state/');
  });

  it('startGame POSTs to start', async () => {
    mocked.mockResolvedValue(state());
    await akinetixService.startGame();
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/start/', { method: 'POST' });
  });

  it('submitAnswer POSTs the answer', async () => {
    mocked.mockResolvedValue(state());
    await akinetixService.submitAnswer('Naruto');
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/answer/', {
      method: 'POST',
      body: JSON.stringify({ answer: 'Naruto' }),
    });
  });

  it('submitConfirmation POSTs correctness and target', async () => {
    mocked.mockResolvedValue(undefined);
    await akinetixService.submitConfirmation(true, 'Naruto');
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/akinetix/confirm/', {
      method: 'POST',
      body: JSON.stringify({ correct: true, actual_target: 'Naruto' }),
    });
  });
});
