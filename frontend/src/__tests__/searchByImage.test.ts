import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../utils/apiClient';
import { searchService } from '../features/search/services/searchService';

vi.mock('../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('searchByImage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('POSTs the image + target as multipart form-data through apiClient (CSRF + auth + toasts)', async () => {
    const results = [{ id: 1 }];
    mocked.mockResolvedValue(results);
    const file = new File(['x'], 'cover.png', { type: 'image/png' });

    const out = await searchService.searchByImage(file);

    expect(mocked).toHaveBeenCalledTimes(1);
    const [url, options] = mocked.mock.calls[0];
    expect(url).toBe('/api/v1/media/search/');
    expect(options).toMatchObject({ method: 'POST', isFormData: true });

    const body = options!.body as FormData;
    expect(body).toBeInstanceOf(FormData);
    expect(body.get('image')).toBe(file);
    expect(body.get('target')).toBe('work');

    expect(out).toBe(results);
  });

  it('sends the requested target', async () => {
    mocked.mockResolvedValue([]);
    const file = new File(['x'], 'portrait.png', { type: 'image/png' });

    await searchService.searchByImage(file, 'character');

    const body = mocked.mock.calls[0][1]!.body as FormData;
    expect(body.get('target')).toBe('character');
  });
});
