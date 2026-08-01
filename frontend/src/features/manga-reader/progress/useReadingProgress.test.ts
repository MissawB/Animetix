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

  // Regression: opening a chapter used to be enough to write. The mount
  // effect armed `{last_page_read: 0, is_read: false}` — currentPageIndex is
  // 0 until the resume lands — and the debounce fired it 1.5 s later with no
  // user action at all, wiping a finished chapter back to unread/page 0.
  it('writes nothing on a passive mount, with no page turn', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { unmount } = renderHook(() =>
      useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
    );

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    expect(put).not.toHaveBeenCalled();

    // Closing the tab during that window must not turn the mount into a write
    // either: the exit flush has nothing pending to send.
    unmount();
    await act(async () => {
      await Promise.resolve();
    });
    expect(put).not.toHaveBeenCalled();
  });

  it('marks the current chapter read on demand, keeping the page reached', async () => {
    const put = vi.spyOn(svc, 'putChapterProgress').mockResolvedValue({});
    const { result } = renderHook(() =>
      useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: true }),
    );

    act(() => {
      useReaderStore.getState().setCurrentPageIndex(1);
    });
    act(() => {
      result.current.markCurrentChapterRead();
    });

    // Immediate — no debounce window — and a single call: "next chapter" must
    // not double-notify the trackers.
    expect(put).toHaveBeenCalledTimes(1);
    expect(put).toHaveBeenCalledWith('m1', '1', { last_page_read: 1, is_read: true });

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    expect(put).toHaveBeenCalledTimes(1);
  });

  it('marks nothing when disabled (anonymous visitor)', () => {
    const put = vi.spyOn(svc, 'putChapterProgress');
    const { result } = renderHook(() =>
      useReadingProgress({ mediaId: 'm1', chapterNumber: '1', enabled: false }),
    );

    act(() => {
      result.current.markCurrentChapterRead();
    });

    expect(put).not.toHaveBeenCalled();
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
