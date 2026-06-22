import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../utils/apiClient';
import { searchMediaByImage } from '../api';

vi.mock('../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mocked = vi.mocked(apiClient);

describe('searchMediaByImage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('POSTs the image as multipart form-data through apiClient (CSRF + auth + toasts)', async () => {
    const results = [{ id: 1 }];
    mocked.mockResolvedValue(results);
    const file = new File(['x'], 'shot.png', { type: 'image/png' });

    const out = await searchMediaByImage(file);

    expect(mocked).toHaveBeenCalledTimes(1);
    const [url, options] = mocked.mock.calls[0];
    expect(url).toBe('/api/v1/search/');
    expect(options).toMatchObject({ method: 'POST', isFormData: true });

    const body = options!.body as FormData;
    expect(body).toBeInstanceOf(FormData);
    expect(body.get('image')).toBe(file);
    expect(body.get('media_type')).toBe('Anime');

    expect(out).toBe(results);
  });

  it('uses the provided media type', async () => {
    mocked.mockResolvedValue([]);
    const file = new File(['x'], 'shot.png', { type: 'image/png' });

    await searchMediaByImage(file, 'Manga');

    const body = mocked.mock.calls[0][1]!.body as FormData;
    expect(body.get('media_type')).toBe('Manga');
  });
});
