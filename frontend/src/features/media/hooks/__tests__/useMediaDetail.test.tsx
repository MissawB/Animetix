import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { mediaService } from '../../services/mediaService';
import { useMediaDetail } from '../useMediaDetail';

vi.mock('../../services/mediaService', () => ({
  mediaService: { getDetail: vi.fn() },
}));
const getDetail = vi.mocked(mediaService.getDetail);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useMediaDetail', () => {
  beforeEach(() => vi.clearAllMocks());

  it('is disabled (no fetch) when params are missing', () => {
    const { result } = renderHook(() => useMediaDetail(undefined, undefined), { wrapper: makeWrapper() });
    expect(getDetail).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('fetches the detail when both params are present', async () => {
    const detail = { id: 7, title: 'Bebop' };
    getDetail.mockResolvedValue(detail);
    const { result } = renderHook(() => useMediaDetail('Anime', '7'), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getDetail).toHaveBeenCalledWith('Anime', '7');
    expect(result.current.data).toEqual(detail);
  });
});
