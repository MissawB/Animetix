import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import * as svc from './progressService';
import { useReaderStore } from '../stores/useReaderStore';
import { useReadingProgress } from './useReadingProgress';

// `@testing-library`'s `waitFor` only auto-advances fake timers when it can
// detect them via a global `jest`, which plain vitest doesn't provide — left
// unshimmed, the "flushes on unmount" test below hangs until the outer
// runner timeout instead of resolving on the already-synchronous flush.
// Scoped to this file only; does not change what any assertion checks.
(globalThis as unknown as { jest?: typeof vi }).jest = vi;

beforeEach(() => {
  vi.useFakeTimers();
  vi.restoreAllMocks();
  useReaderStore.setState({
    pages: [
      { url: 'a', index: 0 },
      { url: 'b', index: 1 },
      { url: 'c', index: 2 },
    ],
    currentPageIndex: 0,
  });
});
afterEach(() => vi.useRealTimers());

describe('useReadingProgress', () => {
  it('debounces writes while pages are turned', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }));

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    act(() => {
      useReaderStore.getState().setCurrentPageIndex(2);
    });
    expect(put).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(1500);
    });
    expect(put).toHaveBeenCalledTimes(1);
    expect(put).toHaveBeenCalledWith('m1', '1', { last_page_read: 2, is_read: true });
  });

  it('flushes the pending write on unmount', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { unmount } = renderHook(() =>
      useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
    );

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    unmount();

    await waitFor(() =>
      expect(put).toHaveBeenCalledWith('m1', '1', {
        last_page_read: 1,
        is_read: false,
      }),
    );
  });

  it('writes nothing at all when disabled', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress');
    renderHook(() => useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: false }));

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(2);
    });
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(put).not.toHaveBeenCalled();
  });
});
