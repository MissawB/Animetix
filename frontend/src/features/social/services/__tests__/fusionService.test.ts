import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { CreativeFusion } from '../../../../types';
import { apiClient } from '../../../../utils/apiClient';
import { fusionService } from '../fusionService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

const makeFusion = (id: number): CreativeFusion => ({ id } as CreativeFusion);

describe('fusionService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getFeed returns an array response directly', async () => {
    const feed = [makeFusion(1), makeFusion(2)];
    mocked.mockResolvedValue(feed);

    const result = await fusionService.getFeed();

    expect(mocked).toHaveBeenCalledWith('/api/v1/fusions/');
    expect(result).toEqual(feed);
  });

  it('getFeed unwraps a paginated results response', async () => {
    const feed = [makeFusion(3)];
    mocked.mockResolvedValue({ results: feed });

    const result = await fusionService.getFeed();

    expect(result).toEqual(feed);
  });

  it('getFeed returns an empty array when results is missing', async () => {
    mocked.mockResolvedValue({});

    const result = await fusionService.getFeed();

    expect(result).toEqual([]);
  });

  it('likeFusion posts to the like endpoint', async () => {
    const res = { status: 'liked', likes_count: 5 };
    mocked.mockResolvedValue(res);

    const result = await fusionService.likeFusion(9);

    expect(mocked).toHaveBeenCalledWith('/api/v1/fusions/9/like/', { method: 'POST' });
    expect(result).toBe(res);
  });

  it('remixFusion posts to the remix endpoint', async () => {
    const fusion = makeFusion(10);
    mocked.mockResolvedValue(fusion);

    const result = await fusionService.remixFusion(10);

    expect(mocked).toHaveBeenCalledWith('/api/v1/fusions/10/remix/', { method: 'POST' });
    expect(result).toBe(fusion);
  });
});
