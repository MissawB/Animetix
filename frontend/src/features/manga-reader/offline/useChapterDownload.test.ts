import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChapterDownload } from './useChapterDownload';
import * as lib from './offlineLibrary';
import { useToastStore } from '../../../store/toastStore';

const META = { mediaId: 'm1', mediaTitle: 'T', chapterNumber: 1, chapterTitle: 'C1' };
const PAGES = [{ number: 0, image_url: 'u0' }];

describe('useChapterDownload', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('starts idle when not downloaded', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('idle'));
  });

  it('starts downloaded when already cached', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(true);
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('downloaded'));
  });

  it('transitions idle -> downloading -> downloaded and tracks progress', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(lib, 'downloadChapter').mockImplementation(async (_m, _p, onProgress) => {
      onProgress?.(0.5);
      onProgress?.(1);
      return {} as lib.DownloadedChapter;
    });
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('idle'));
    await act(async () => {
      await result.current.download();
    });
    expect(result.current.status).toBe('downloaded');
    expect(result.current.progress).toBe(1);
  });

  it('sets error status with message on failure', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(lib, 'downloadChapter').mockRejectedValue(new lib.OfflineQuotaError());
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('idle'));
    await act(async () => {
      await result.current.download();
    });
    expect(result.current.status).toBe('error');
    expect(result.current.error).toContain('stockage');
  });

  it('toasts an error on download failure', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(false);
    vi.spyOn(lib, 'downloadChapter').mockRejectedValue(new lib.OfflineQuotaError());
    const addToast = vi
      .spyOn(useToastStore.getState(), 'addToast')
      .mockImplementation(() => {});
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('idle'));
    await act(async () => {
      await result.current.download();
    });
    expect(addToast).toHaveBeenCalledWith(expect.stringContaining('stockage'), 'error');
  });

  it('remove() deletes and returns to idle', async () => {
    vi.spyOn(lib, 'isChapterDownloaded').mockResolvedValue(true);
    const del = vi.spyOn(lib, 'deleteChapter').mockResolvedValue();
    const { result } = renderHook(() => useChapterDownload(META, PAGES));
    await waitFor(() => expect(result.current.status).toBe('downloaded'));
    await act(async () => {
      await result.current.remove();
    });
    expect(del).toHaveBeenCalledWith('m1', 1);
    expect(result.current.status).toBe('idle');
    expect(result.current.progress).toBe(0);
    expect(result.current.error).toBeNull();
  });
});
