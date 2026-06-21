import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { utilsService } from '../utilsService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('utilsService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getDaily fetches the daily-challenge endpoint', async () => {
    const data = { challenge: 'today' };
    mocked.mockResolvedValue(data);

    const result = await utilsService.getDaily();

    expect(mocked).toHaveBeenCalledWith('/api/v1/daily-challenge/');
    expect(result).toBe(data);
  });

  it('getConfig fetches the custom-config endpoint', async () => {
    const data = { config: true };
    mocked.mockResolvedValue(data);

    const result = await utilsService.getConfig();

    expect(mocked).toHaveBeenCalledWith('/api/v1/custom-config/');
    expect(result).toBe(data);
  });
});
