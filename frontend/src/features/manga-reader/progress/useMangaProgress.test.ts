import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as apiMod from '../../../utils/apiClient';
import { useMangaProgress } from './useMangaProgress';

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client }, children);
};

beforeEach(() => vi.restoreAllMocks());

describe('useMangaProgress', () => {
  it('indexes chapters by number', async () => {
    vi.spyOn(apiMod, 'apiClient').mockResolvedValue({
      chapters: [{ number: 164.2, is_read: false, last_page_read: 11, page_count: 83 }],
      resume: { chapter_number: 164.2, last_page_read: 11 },
      read_count: 0,
      total_count: 1,
    });

    const { result } = renderHook(() => useMangaProgress('m1', true), { wrapper });

    await waitFor(() => expect(result.current.data).toBeTruthy());
    expect(result.current.byChapter.get(164.2)?.last_page_read).toBe(11);
  });

  it('never calls the API when disabled (anonymous visitor)', async () => {
    const api = vi.spyOn(apiMod, 'apiClient');
    const { result } = renderHook(() => useMangaProgress('m1', false), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(api).not.toHaveBeenCalled();
  });

  it('treats a 204 (manga never imported) as an empty progress', async () => {
    vi.spyOn(apiMod, 'apiClient').mockResolvedValue(null);
    const { result } = renderHook(() => useMangaProgress('m1', true), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.byChapter.size).toBe(0);
  });

  it('refetch() with undefined mediaId makes no API call', async () => {
    const api = vi.spyOn(apiMod, 'apiClient');
    const { result } = renderHook(() => useMangaProgress(undefined, true), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Explicit refetch() should not emit a network call when mediaId is undefined
    await result.current.refetch();

    expect(api).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });
});
