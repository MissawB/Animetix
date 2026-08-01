import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as apiMod from '../../../utils/apiClient';
import { useResumeReadingPosition } from './useResumeReadingPosition';

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client }, children);
};

beforeEach(() => vi.restoreAllMocks());

describe('useResumeReadingPosition', () => {
  // Regression: Suwayomi (chapter pages) can resolve before Django
  // (/progress/). If the once-per-chapter guard is consumed the moment
  // pages are ready — instead of waiting for the progress query to settle —
  // the resume is silently skipped forever once the saved position finally
  // arrives: the reader would restart at page 1 even though the user had
  // stopped at page 40.
  it('still resumes once the progress query settles, even when pages were ready first', async () => {
    let resolveApi: (value: unknown) => void = () => {};
    const pending = new Promise((resolve) => {
      resolveApi = resolve;
    });
    vi.spyOn(apiMod, 'apiClient').mockReturnValue(pending as Promise<unknown>);

    const setCurrentPageIndex = vi.fn();

    renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: 50, // pages already loaded
          setCurrentPageIndex,
        }),
      { wrapper },
    );

    // Progress request still in flight: nothing to resume from yet.
    expect(setCurrentPageIndex).not.toHaveBeenCalled();

    await act(async () => {
      resolveApi({
        chapters: [{ number: 5, is_read: false, last_page_read: 39, page_count: 50 }],
        resume: { chapter_number: 5, last_page_read: 39 },
        read_count: 0,
        total_count: 1,
      });
      await pending;
    });

    await waitFor(() => expect(setCurrentPageIndex).toHaveBeenCalledWith(39));
  });

  // `isResolved` is what gates the *writer* hook (useReadingProgress): while
  // it is false, currentPageIndex is a placeholder 0 rather than the reader's
  // real position, and writing it would erase the progress being restored.
  it('reports isResolved only once the resume question is settled', async () => {
    let resolveApi: (value: unknown) => void = () => {};
    const pending = new Promise((resolve) => {
      resolveApi = resolve;
    });
    vi.spyOn(apiMod, 'apiClient').mockReturnValue(pending as Promise<unknown>);

    const { result, rerender } = renderHook(
      (props: { readerPagesLength: number }) =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: true,
          isAuthLoading: false,
          readerPagesLength: props.readerPagesLength,
          setCurrentPageIndex: vi.fn(),
        }),
      { wrapper, initialProps: { readerPagesLength: 0 } },
    );

    // No pages yet, and no progress yet.
    expect(result.current.isResolved).toBe(false);

    rerender({ readerPagesLength: 50 });
    // Pages ready but /progress/ still in flight: still unresolved.
    expect(result.current.isResolved).toBe(false);

    await act(async () => {
      resolveApi({
        chapters: [{ number: 5, is_read: true, last_page_read: 82, page_count: 83 }],
        resume: null,
        read_count: 1,
        total_count: 1,
      });
      await pending;
    });

    await waitFor(() => expect(result.current.isResolved).toBe(true));
  });

  // Guards the new "wait for isFetched" branch: for an anonymous visitor
  // useMangaProgress never runs its query (enabled=false), so isFetched
  // would never become true — the hook must not wait on it forever.
  it('does not wait on the progress query for an anonymous visitor', async () => {
    const api = vi.spyOn(apiMod, 'apiClient');
    const setCurrentPageIndex = vi.fn();

    renderHook(
      () =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: false,
          isAuthLoading: false,
          readerPagesLength: 50,
          setCurrentPageIndex,
        }),
      { wrapper },
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(api).not.toHaveBeenCalled();
    expect(setCurrentPageIndex).not.toHaveBeenCalled();
  });

  // Regression: a deep-link render (favorite, F5, shared link) mounts before
  // Firebase's onAuthStateChanged/getRedirectResult has resolved. authStore
  // starts as { isAuthenticated: false, isLoading: true } on every app load
  // (see store/authStore.ts), so a naive `isAuthenticated && !progressFetched`
  // gate reads "anonymous, nothing to wait for" and consumes the guard on
  // the spot — then the effect exits on resumedRef alone once auth actually
  // resolves to logged-in, and the real saved position never gets applied.
  it('still resumes once auth resolves to logged-in, even if it read as anonymous at first render', async () => {
    vi.spyOn(apiMod, 'apiClient').mockResolvedValue({
      chapters: [{ number: 5, is_read: false, last_page_read: 39, page_count: 50 }],
      resume: { chapter_number: 5, last_page_read: 39 },
      read_count: 0,
      total_count: 1,
    });

    const setCurrentPageIndex = vi.fn();

    const { rerender } = renderHook(
      (props: { isAuthenticated: boolean; isAuthLoading: boolean }) =>
        useResumeReadingPosition({
          mediaId: 'm1',
          chapterId: '5',
          isAuthenticated: props.isAuthenticated,
          isAuthLoading: props.isAuthLoading,
          readerPagesLength: 50, // pages already loaded
          setCurrentPageIndex,
        }),
      { wrapper, initialProps: { isAuthenticated: false, isAuthLoading: true } },
    );

    // Auth not resolved yet: must not treat this as "anonymous, nothing to
    // resume" and burn the guard.
    expect(setCurrentPageIndex).not.toHaveBeenCalled();

    await act(async () => {
      rerender({ isAuthenticated: true, isAuthLoading: false });
      await Promise.resolve();
    });

    await waitFor(() => expect(setCurrentPageIndex).toHaveBeenCalledWith(39));
  });
});
