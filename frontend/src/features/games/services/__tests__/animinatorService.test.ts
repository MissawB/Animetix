import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { animinatorService, type AniminatorResponse } from '../animinatorService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

describe('animinatorService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('ask POSTs the question and returns the response', async () => {
    const res: AniminatorResponse = { answer: 'Yes', questions_left: 3 };
    mocked.mockResolvedValue(res);

    const out = await animinatorService.ask('Is it an anime?');

    expect(out).toBe(res);
    expect(mocked).toHaveBeenCalledWith('/api/v1/game/animinator/ask/', {
      method: 'POST',
      body: JSON.stringify({ question: 'Is it an anime?' }),
    });
  });
});
