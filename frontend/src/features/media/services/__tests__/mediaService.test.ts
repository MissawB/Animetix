import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { mediaService } from '../mediaService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

describe('mediaService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getDetail reads the media detail endpoint', async () => {
    const detail = { id: 42, title: 'Akira' };
    mocked.mockResolvedValue(detail);

    const out = await mediaService.getDetail('Anime', '42');

    expect(out).toBe(detail);
    expect(mocked).toHaveBeenCalledWith('/api/v1/media/Anime/42/');
  });
});
