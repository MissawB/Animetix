import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useChapterPages } from './useChapterPages';
import * as lib from './offlineLibrary';
import * as apiMod from '../../../utils/apiClient';

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:fake'),
    revokeObjectURL: vi.fn(),
  });
});

describe('useChapterPages', () => {
  it('serves pages from IndexedDB blobs when downloaded (no network)', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(true);
    vi.spyOn(lib, 'getChapterPageBlobs').mockResolvedValue([new Blob(['a']), new Blob(['b'])]);
    const api = vi.spyOn(apiMod, 'apiClient');

    const { result } = renderHook(() => useChapterPages('m1', '3'));
    await waitFor(() => expect(result.current.source).toBe('offline'));
    expect(result.current.pages).toHaveLength(2);
    expect(result.current.pages[0]).toEqual({ url: 'blob:fake', index: 0 });
    expect(api).not.toHaveBeenCalled();
  });

  it('falls back to the network fetch when not downloaded', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(apiMod, 'apiClient').mockResolvedValue({
      pages: [{ image_url: 'http://h/p0.jpg', number: 0 }],
    });
    const { result } = renderHook(() => useChapterPages('m1', '3'));
    await waitFor(() => expect(result.current.source).toBe('network'));
    expect(result.current.pages[0]).toEqual({ url: 'http://h/p0.jpg', index: 0 });
  });

  it('reports unavailable when offline and not downloaded', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(apiMod, 'apiClient').mockRejectedValue(new TypeError('Failed to fetch'));
    const { result } = renderHook(() => useChapterPages('m1', '3'));
    await waitFor(() => expect(result.current.source).toBe('unavailable'));
    expect(result.current.pages).toHaveLength(0);
  });
});
