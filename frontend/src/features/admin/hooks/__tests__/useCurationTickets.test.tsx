import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '../../../../utils/apiClient';
import { useCurationTickets } from '../useCurationTickets';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mocked = vi.mocked(apiClient);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useCurationTickets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.mockImplementation((url: string) => {
      if (url === '/api/v1/curation/') return Promise.resolve({ results: [{ id: 1 }] });
      if (url === '/api/v1/curation/stats/') return Promise.resolve({ open: 3 });
      return Promise.resolve({});
    });
  });

  it('exposes unwrapped tickets and stats', async () => {
    const { result } = renderHook(() => useCurationTickets(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.tickets).toEqual([{ id: 1 }]);
    await waitFor(() => expect(result.current.stats).toEqual({ open: 3 }));
  });

  it('resolve POSTs to the resolve endpoint', async () => {
    const { result } = renderHook(() => useCurationTickets(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.resolve(7);
    });

    await waitFor(() =>
      expect(mocked).toHaveBeenCalledWith('/api/v1/curation/7/resolve/', { method: 'POST' }),
    );
  });
});
