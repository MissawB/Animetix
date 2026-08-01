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
});
