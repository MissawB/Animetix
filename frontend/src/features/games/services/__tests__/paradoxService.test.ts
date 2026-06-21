import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ParadoxState } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { paradoxService } from '../paradoxService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeState = (): ParadoxState => ({} as ParadoxState);

describe('paradoxService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getState calls the state endpoint and returns the value', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await paradoxService.getState();

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/paradox/state/');
    expect(result).toBe(state);
  });

  it('submit posts the intruder id to the move endpoint', async () => {
    const state = makeState();
    mocked.mockResolvedValue(state);

    const result = await paradoxService.submit({ intruder_id: 7 });

    expect(mocked).toHaveBeenCalledWith('/api/v1/game/paradox/move/', {
      method: 'POST',
      body: JSON.stringify({ intruder_id: 7 }),
    });
    expect(result).toBe(state);
  });
});
