import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { goldDatasetService } from '../goldDatasetService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('goldDatasetService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getList unwraps a paginated results response', async () => {
    const rows = [{ id: 1 }];
    mocked.mockResolvedValue({ results: rows });

    const result = await goldDatasetService.getList();

    expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/gold-dataset/');
    expect(result).toBe(rows);
  });

  it('getList returns the raw data when results is absent', async () => {
    const rows = [{ id: 2 }];
    mocked.mockResolvedValue(rows);

    const result = await goldDatasetService.getList();

    expect(result).toBe(rows);
  });

  it('validateEntry posts to the validate endpoint', async () => {
    const data = { ok: true };
    mocked.mockResolvedValue(data);

    const result = await goldDatasetService.validateEntry(8);

    expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/gold-dataset/8/validate/', { method: 'POST' });
    expect(result).toBe(data);
  });

  it('syncPositiveFeedback posts to the sync endpoint', async () => {
    const data = { synced: 3 };
    mocked.mockResolvedValue(data);

    const result = await goldDatasetService.syncPositiveFeedback();

    expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/gold-dataset/sync_positive_feedback/', { method: 'POST' });
    expect(result).toBe(data);
  });

  it('deleteEntry sends a DELETE to the entry endpoint', async () => {
    mocked.mockResolvedValue(null);

    const result = await goldDatasetService.deleteEntry(8);

    expect(mocked).toHaveBeenCalledWith('/api/v1/mlops/gold-dataset/8/', { method: 'DELETE' });
    expect(result).toBeNull();
  });
});
