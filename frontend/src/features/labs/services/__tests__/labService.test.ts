import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../../../utils/apiClient';
import { labService } from '../labService';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('labService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getLatent fetches the latent endpoint', async () => {
    const data = { latent: true };
    mocked.mockResolvedValue(data);

    const result = await labService.getLatent();

    expect(mocked).toHaveBeenCalledWith('/api/v1/lab/latent/');
    expect(result).toBe(data);
  });

  it('getManga fetches the manga endpoint', async () => {
    const data = { manga: true };
    mocked.mockResolvedValue(data);

    const result = await labService.getManga();

    expect(mocked).toHaveBeenCalledWith('/api/v1/lab/manga/');
    expect(result).toBe(data);
  });

  it('getSpatial fetches the spatial endpoint', async () => {
    const data = { spatial: true };
    mocked.mockResolvedValue(data);

    const result = await labService.getSpatial();

    expect(mocked).toHaveBeenCalledWith('/api/v1/lab/spatial/');
    expect(result).toBe(data);
  });

  it('runDiagnostics posts the prompt', async () => {
    const data = { ok: true };
    mocked.mockResolvedValue(data);

    const result = await labService.runDiagnostics('hello');

    expect(mocked).toHaveBeenCalledWith('/api/v1/labs/diagnostics/', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'hello' }),
    });
    expect(result).toBe(data);
  });
});
